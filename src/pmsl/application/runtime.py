"""统一管理内嵌与外部控制台的启动、指令、停服和运行快照。"""

import os
import subprocess
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional

from pmsl.domain.errors import PmslError
from pmsl.domain.models import LaunchPlan
from pmsl.domain.runtime import LogSnapshot, RuntimeSnapshot
from pmsl.domain.states import ProcessState
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.process import MAX_LINE_LENGTH, MAX_LINES, ProcessSession
from pmsl.infrastructure.runner import runner_arguments
from pmsl.infrastructure.runtime_tasks import RuntimeTask, read_document
from pmsl.infrastructure.windows import process_identity


class ServerRuntime:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        self.task: Optional[RuntimeTask] = None
        self.session: Optional[ProcessSession] = None
        self.runner: Any = None
        self._snapshot: Optional[RuntimeSnapshot] = None
        self._logs = LogSnapshot(0, ())
        self._sequence = 0
        self._commands: List[Dict[str, Any]] = []
        self._identity: Dict[str, object] = {}
        self._last_sync = 0.0
        self._published: Any = None

    def ensure_no_unconfirmed_tasks(self) -> None:
        directory = self.paths.data("runtime")
        if not directory.exists():
            return
        for launch in directory.glob("*/launch.json"):
            descriptor = read_document(self.paths, launch)
            task_id, token = descriptor.get("task_id"), descriptor.get("token")
            if not isinstance(task_id, str) or not isinstance(token, str):
                raise PmslError("旧运行任务缺少身份，请人工检查。")
            task = RuntimeTask(self.paths, task_id, token)
            if self.task is not None and task.id == self.task.id:
                continue
            status_path = task.directory / "status.json"
            if not status_path.exists() or task.read("status.json").get("state") not in {
                ProcessState.STOPPED.value,
                ProcessState.FAILED.value,
            }:
                raise PmslError(
                    "发现未确认结束的运行任务 %s，请检查其控制台和状态文件后处理；"
                    "不会根据保存的 PID 强制结束进程。" % task.id
                )

    def start(
        self, server_id: str, name: str, plan: LaunchPlan, save_log: bool = False
    ) -> RuntimeSnapshot:
        current = self.snapshot()
        if current is not None and current.active:
            raise PmslError("已有服务器正在运行，请先正常停服。")
        if self.runner is not None and self.runner.poll() is None:
            raise PmslError("外部控制台正在结束，请等待其关闭后再启动。")
        self.ensure_no_unconfirmed_tasks()
        self.close()
        cwd = self.paths.inside(plan.cwd)
        if not cwd.is_dir() or not Path(plan.executable).is_file():
            raise PmslError("服务器工作目录或执行文件不存在。")
        self.task, digest = RuntimeTask.create(self.paths, server_id, name, plan, save_log)
        self._snapshot = RuntimeSnapshot(self.task.id, server_id, ProcessState.STARTING)
        self._logs = LogSnapshot(0, ())
        self._sequence = 0
        self._commands = []
        self._identity = {}
        self._last_sync = 0
        self._published = None
        self.task.publish(self._snapshot, {}, 0, self._logs)
        try:
            plan, _ = self.task.load_plan(digest)
            if plan.external_console:
                temporary = self.paths.data("tmp")
                temporary.mkdir(parents=True, exist_ok=True)
                self.runner = subprocess.Popen(
                    runner_arguments(self.task, digest),
                    cwd=str(self.paths.program_dir),
                    env=dict(os.environ, TEMP=str(temporary), TMP=str(temporary)),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=0x10 if os.name == "nt" else 0,
                )
                self._identity = process_identity(self.runner.pid)
            else:
                self.task.claim(digest)
                self.session = ProcessSession(self.paths, self.task.id, server_id, plan, save_log)
                self.session.start()
                self._identity = process_identity(self.session.process.pid)
            result = self.update(force=True)
            assert result is not None
            return result
        except BaseException as exc:
            if self.session is not None:
                self.session.close()
                self.session = None
            state = ProcessState.FAILED
            if self.runner is not None and self.runner.poll() is None:
                # runner 尚未退出时保留活动状态，阻止再次启动服务器。
                state = ProcessState.STARTING
                self._send("force")
            self._snapshot = replace(self._snapshot, state=state, error=str(exc))
            self.task.publish(self._snapshot, self._identity, 0, self._logs)
            raise

    def snapshot(self) -> Optional[RuntimeSnapshot]:
        if self.session is not None:
            self._snapshot = self.session.snapshot()
        return self._snapshot

    def logs(self) -> LogSnapshot:
        return self.session.logs() if self.session is not None else self._logs

    def update(self, force: bool = False) -> Optional[RuntimeSnapshot]:
        if self.task is None:
            return None
        now = time.monotonic()
        if not force and now - self._last_sync < 0.2:
            return self.snapshot()
        self._last_sync = now
        if self.session is not None:
            self._snapshot = self.session.snapshot()
            if not self._snapshot.active:
                self.session.close()
            logs = self.session.logs()
            signature = (self._snapshot, logs.revision)
            if signature != self._published:
                self.task.publish(self._snapshot, self._identity, 0, logs)
                self._published = signature
        elif self.runner is not None:
            # 先检查 runner 是否退出，再读取其最终状态，避免误判正常停服。
            runner_exited = self.runner.poll() is not None
            document = self.task.read("status.json")
            identity = document.get("identity", {})
            if identity and identity != self._identity:
                raise PmslError("外部运行任务的进程身份已改变。")
            state = ProcessState(document["state"])
            self._snapshot = RuntimeSnapshot(
                self.task.id,
                document["server_id"],
                state,
                document.get("pid"),
                document.get("exit_code"),
                document.get("ready", False),
                document.get("stop_timed_out", False),
                document.get("error"),
            )
            output = self.task.read("output.json")
            lines = output.get("lines")
            if (
                not isinstance(lines, list)
                or len(lines) > MAX_LINES
                or not all(isinstance(line, str) and len(line) <= MAX_LINE_LENGTH for line in lines)
            ):
                raise PmslError("外部运行任务的日志格式无效。")
            if type(output.get("revision")) is not int or output["revision"] < 0:
                raise PmslError("外部运行任务的日志版本无效。")
            self._logs = LogSnapshot(output["revision"], tuple(lines))
            self._commands = [
                command
                for command in self._commands
                if command["sequence"] > document.get("ack", 0)
            ]
            if runner_exited and self._snapshot.active:
                self._snapshot = replace(
                    self._snapshot, state=ProcessState.FAILED, error="外部运行任务意外退出。"
                )
                self.task.publish(self._snapshot, self._identity, 0, self._logs)
        return self._snapshot

    def _send(self, kind: str, value: str = "") -> None:
        snapshot = self.snapshot()
        if snapshot is None or not snapshot.active:
            raise PmslError("服务器进程已经退出。")
        if len(self._commands) >= 256:
            raise PmslError("指令队列已满，请稍后重试。")
        assert self.task is not None
        sequence = self._sequence + 1
        commands = [*self._commands, dict(sequence=sequence, kind=kind, value=value)]
        self.task.write("commands.json", dict(commands=commands))
        self._sequence, self._commands = sequence, commands

    def send_command(self, command: str) -> None:
        if (
            not command
            or len(command) > MAX_LINE_LENGTH
            or any(character in command for character in "\r\n\x00")
        ):
            raise PmslError("指令必须为不超过 %d 个字符的单行文本。" % MAX_LINE_LENGTH)
        if command == "stop":
            self.request_stop()
        elif self.session is not None:
            self.session.send_command(command)
        else:
            self._send("input", command)

    def request_stop(self) -> None:
        snapshot = self.snapshot()
        if snapshot is None or not snapshot.active or snapshot.state is ProcessState.STOPPING:
            return
        if self.session is not None:
            self.session.request_stop()
        elif not any(command["kind"] == "stop" for command in self._commands):
            self._send("stop")

    def force_stop(self) -> None:
        snapshot = self.snapshot()
        if snapshot is None or not snapshot.active:
            return
        if self.session is not None:
            self.session.force_stop()
        else:
            self._send("force")

    def close(self) -> None:
        if self.session is not None:
            self.session.close()
            self.update(force=True)
            self._logs = self.session.logs()
            self.session = None
        # 外部进程树由 runner 清理，此处仅回收已退出的 runner。
        if self.runner is not None and self.runner.poll() is not None:
            self.runner.wait()
            self.runner = None
