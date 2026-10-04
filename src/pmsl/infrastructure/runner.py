"""运行独立服务器任务，在控制台与启动器之间传递指令、状态和日志。"""

import os
import queue
import sys
import threading
import time
from typing import Any

from pmsl.domain.errors import PmslError
from pmsl.domain.runtime import RuntimeSnapshot
from pmsl.domain.states import ProcessState
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.process import ProcessSession
from pmsl.infrastructure.runtime_tasks import RuntimeTask
from pmsl.infrastructure.windows import open_console, process_identity


def run_task(paths: AppPaths, task_id: str, token: str, digest: str) -> int:
    task = RuntimeTask(paths, task_id, token)
    plan, document = task.load_plan(digest)
    # 独占创建认领文件，防止同一任务重复启动。
    task.claim(digest)
    session = ProcessSession(paths, task_id, document["server_id"], plan, document["save_log"])
    identity = process_identity(os.getpid())
    commands: queue.Queue = queue.Queue(maxsize=256)
    ack = 0

    def read_console() -> None:
        try:
            while session.snapshot().active:
                line = sys.stdin.readline()
                if not line:
                    break
                try:
                    commands.put(line.rstrip("\r\n"), timeout=0.1)
                except queue.Full:
                    print("指令过多，请稍后重试。", flush=True)
        except (OSError, ValueError):
            pass

    try:
        if plan.external_console:
            open_console()
        session.start()
        if plan.external_console:
            threading.Thread(target=read_console, daemon=True, name="pmsl-console-input").start()
        last_output = 0
        while True:
            packet_path = task.directory / "commands.json"
            if packet_path.exists():
                packet = task.read("commands.json")
                packets = packet.get("commands", [])
                if not isinstance(packets, list) or len(packets) > 256:
                    raise PmslError("运行任务指令队列无效。")
                for item in packets:
                    if not isinstance(item, dict) or type(item.get("sequence")) is not int:
                        raise PmslError("运行任务指令格式无效。")
                    if item["sequence"] <= ack:
                        continue
                    if item["sequence"] != ack + 1:
                        raise PmslError("运行任务指令顺序不匹配。")
                    if item.get("kind") == "stop":
                        session.request_stop()
                    elif item.get("kind") == "force":
                        session.force_stop()
                    elif item.get("kind") == "input" and isinstance(item.get("value"), str):
                        session.send_command(item["value"])
                    else:
                        raise PmslError("未知运行任务指令。")
                    ack = item["sequence"]
            for _ in range(32):
                try:
                    line = commands.get_nowait()
                except queue.Empty:
                    break
                try:
                    if line == "stop":
                        session.request_stop()
                    else:
                        session.send_command(line)
                except PmslError as exc:
                    print(str(exc), flush=True)
            logs = session.logs()
            if plan.external_console and logs.revision != last_output:
                count = min(logs.revision - last_output, len(logs.lines))
                for line in logs.lines[-count:]:
                    print(line, flush=True)
                last_output = logs.revision
            snapshot = session.snapshot()
            task.publish(snapshot, identity, ack, logs)
            if not snapshot.active:
                break
            time.sleep(0.2)
        session.close()
        task.publish(session.snapshot(), identity, ack, session.logs())
        if plan.external_console:
            print(
                "\n\033[1;32m服务器已关闭,你可以关闭此界面!!\033[0m\n"
                "\033[1m此界面将在 \033[1;31m10\033[0m\033[1m 秒后自动关闭...\033[0m",
                flush=True,
            )
            time.sleep(10)
        return snapshot.exit_code or 0
    except (OSError, ValueError, PmslError) as exc:
        session.close()
        failed = RuntimeSnapshot(
            task_id, document["server_id"], ProcessState.FAILED, error=str(exc)
        )
        task.publish(failed, identity, ack, session.logs())
        return 1
    finally:
        session.close()


def runner_arguments(task: RuntimeTask, digest: str) -> Any:
    args = ["--runner", task.id, "--task-token", task.token, "--plan-hash", digest]
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    # 数据目录缺少入口时，从源码位置定位启动脚本。
    source = task.paths.program_dir / "PyMinecraftServerLanucher.py"
    if not source.is_file():
        from pathlib import Path

        source = Path(__file__).resolve().parents[3] / "PyMinecraftServerLanucher.py"
    return [sys.executable, "-B", str(source), *args, "--program-dir", str(task.paths.program_dir)]
