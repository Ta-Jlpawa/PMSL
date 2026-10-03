"""实际进程、增量解码和有界日志；不导入界面。"""

import codecs
import os
import re
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Optional

from pmsl.domain.errors import PmslError
from pmsl.domain.models import LaunchPlan
from pmsl.domain.runtime import LogSnapshot, RuntimeSnapshot
from pmsl.domain.states import ProcessState
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.windows import ProcessTree

MAX_LINES = 5000
MAX_LINE_LENGTH = 2048


class ProcessSession:
    def __init__(
        self,
        paths: AppPaths,
        task_id: str,
        server_id: str,
        plan: LaunchPlan,
        save_log: bool = False,
    ) -> None:
        self.paths = paths
        self.task_id = task_id
        self.server_id = server_id
        self.plan = plan
        self.process: Any = None
        self.tree = ProcessTree()
        self.reader: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._input_lock = threading.Lock()
        self._lines: Deque[str] = deque(maxlen=MAX_LINES)
        self._revision = 0
        self._ready = False
        self._stop_at: Optional[float] = None
        self._error: Optional[str] = None
        self._reader_done = threading.Event()
        self._log: Any = None
        self._log_path: Optional[Path] = paths.data("logs/%s.log" % task_id) if save_log else None

    def start(self) -> None:
        if self.process is not None:
            raise PmslError("运行会话已经启动，不能重复创建进程。")
        cwd = self.paths.inside(self.plan.cwd)
        if not cwd.is_dir():
            raise PmslError("服务器工作目录不存在。")
        codecs.lookup(self.plan.encoding)
        temporary = self.paths.data("tmp")
        temporary.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ)
        environment.update(self.plan.environment)
        environment.update(TEMP=str(temporary), TMP=str(temporary))
        if self._log_path is not None:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log = self._log_path.open("ab")
        try:
            self.process = subprocess.Popen(
                [self.plan.executable, *self.plan.arguments],
                cwd=str(cwd),
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                shell=False,
                creationflags=(0x08000000 | 4) if os.name == "nt" else 0,
                start_new_session=os.name != "nt",
            )
            # 先挂入进程树再恢复线程，防止 BAT 在登记之前派生 Java。
            self.tree.attach_and_resume(self.process)
            self.reader = threading.Thread(target=self._read, daemon=True, name="pmsl-output")
            self.reader.start()
        except BaseException:
            if self.process is not None:
                self.process.kill()
                self.process.wait(timeout=5)
            self.close()
            raise

    def _append(self, line: str) -> None:
        line = line.rstrip("\r")[:MAX_LINE_LENGTH]
        with self._lock:
            self._lines.append(line)
            self._revision += 1
            if re.search(r"\bDone \(.+\)!", line):
                self._ready = True
        if self._log is not None:
            self._log.write((line + "\n").encode("utf-8", "replace"))
            self._log.flush()
            if self._log.tell() >= 5 * 1024 * 1024:
                self._log.close()
                assert self._log_path is not None
                older = self.paths.inside(str(self._log_path) + ".2")
                previous = self.paths.inside(str(self._log_path) + ".1")
                if previous.exists():
                    os.replace(str(previous), str(older))
                os.replace(str(self._log_path), str(previous))
                self._log = self._log_path.open("ab")

    def _read(self) -> None:
        decoder = codecs.getincrementaldecoder(self.plan.encoding)(errors="replace")
        pending = ""
        try:
            while True:
                block = self.process.stdout.read(4096)
                pending += decoder.decode(block, final=not block)
                while "\n" in pending or len(pending) > MAX_LINE_LENGTH:
                    end = pending.find("\n")
                    if end < 0 or end > MAX_LINE_LENGTH:
                        end = MAX_LINE_LENGTH
                        step = end
                    else:
                        step = end + 1
                    self._append(pending[:end])
                    pending = pending[step:]
                if not block:
                    break
            if pending:
                self._append(pending)
        except (OSError, ValueError) as exc:
            self._error = "日志读取失败：%s" % exc
        finally:
            self._reader_done.set()

    def send_command(self, command: str) -> None:
        if not self.snapshot().active:
            raise PmslError("服务器进程已经退出。")
        if not command or len(command) > MAX_LINE_LENGTH or any(c in command for c in "\r\n\x00"):
            raise PmslError("指令必须为不超过 %d 个字符的单行文本。" % MAX_LINE_LENGTH)
        try:
            payload = (command + "\n").encode(self.plan.encoding)
            with self._input_lock:
                self.process.stdin.write(payload)
                self.process.stdin.flush()
        except (OSError, ValueError, UnicodeError) as exc:
            raise PmslError("指令发送失败：%s" % exc) from exc
        # 日志落盘只有读取线程负责，避免与滚动写入并发。
        with self._lock:
            self._lines.append("> " + command)
            self._revision += 1

    def request_stop(self) -> None:
        if not self.snapshot().active or self._stop_at is not None:
            return
        self.send_command("stop")
        self._stop_at = time.monotonic()

    def force_stop(self) -> None:
        if self.process is None:
            return
        if os.name == "nt":
            self.tree.close()
        else:
            try:
                getattr(os, "killpg")(self.process.pid, getattr(signal, "SIGKILL"))
            except ProcessLookupError:
                pass
        self.process.wait(timeout=5)

    def snapshot(self) -> RuntimeSnapshot:
        code = self.process.poll() if self.process is not None else None
        state = ProcessState.STARTING
        if code is not None:
            state = ProcessState.STOPPED if code == 0 else ProcessState.FAILED
        elif self._stop_at is not None:
            state = ProcessState.STOPPING
        elif self._ready:
            state = ProcessState.RUNNING
        return RuntimeSnapshot(
            self.task_id,
            self.server_id,
            state,
            self.process.pid if self.process is not None else None,
            code,
            self._ready,
            self._stop_at is not None and code is None and time.monotonic() - self._stop_at >= 30,
            self._error,
        )

    def logs(self) -> LogSnapshot:
        with self._lock:
            return LogSnapshot(self._revision, tuple(self._lines))

    def close(self) -> None:
        # 仅处理此对象持有的进程树，不按保存的 PID 查杀。
        self.tree.close()
        if self.process is not None:
            if self.process.poll() is None:
                self.force_stop()
            if self.reader is not None:
                self.reader.join(timeout=2)
            for stream in (self.process.stdin, self.process.stdout):
                if stream is not None:
                    stream.close()
        if self._log is not None:
            self._log.close()
            self._log = None
