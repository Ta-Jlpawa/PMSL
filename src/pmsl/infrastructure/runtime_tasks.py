"""任务独立启动描述、状态和有界本地指令通信。"""

import codecs
import hashlib
import json
import re
import secrets
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Tuple
from uuid import uuid4

from pmsl.domain.errors import PmslError
from pmsl.domain.models import LaunchPlan
from pmsl.domain.runtime import LogSnapshot, RuntimeSnapshot
from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.windows import protect_directory


def read_document(paths: AppPaths, path: Path) -> Dict[str, Any]:
    target = paths.inside(path)
    if target.stat().st_size > 32 * 1024 * 1024:
        raise PmslError("运行任务文件超过大小限制。")
    try:
        result = json.loads(target.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise PmslError("运行任务文件已损坏。") from exc
    if (
        not isinstance(result, dict)
        or type(result.get("schema_version")) is not int
        or result.get("schema_version") != 1
    ):
        raise PmslError("运行任务文件版本不受支持。")
    return result


def write_document(paths: AppPaths, path: Path, value: Dict[str, Any]) -> None:
    payload = json.dumps(dict(value, schema_version=1), ensure_ascii=False).encode("utf-8")
    atomic_write(paths, path, payload)


class RuntimeTask:
    def __init__(self, paths: AppPaths, task_id: str, token: str) -> None:
        if (
            not isinstance(task_id, str)
            or not isinstance(token, str)
            or (
                re.fullmatch(r"[0-9a-f]{32}", task_id) is None
                or re.fullmatch(r"[0-9a-f]{64}", token) is None
            )
        ):
            raise PmslError("运行任务身份无效。")
        self.paths = paths
        self.id = task_id
        self.token = token
        self.directory = paths.data("runtime/" + task_id)

    @classmethod
    def create(
        cls, paths: AppPaths, server_id: str, name: str, plan: LaunchPlan, save_log: bool
    ) -> Tuple["RuntimeTask", str]:
        task = cls(paths, uuid4().hex, secrets.token_hex(32))
        task.directory.mkdir(parents=True, exist_ok=False)
        protect_directory(str(task.directory))
        document = dict(
            task_id=task.id,
            token=task.token,
            server_id=server_id,
            name=name,
            plan=asdict(plan),
            save_log=save_log,
        )
        write_document(paths, task.directory / "launch.json", document)
        digest = hashlib.sha256((task.directory / "launch.json").read_bytes()).hexdigest()
        return task, digest

    def read(self, filename: str) -> Dict[str, Any]:
        document = read_document(self.paths, self.directory / filename)
        if document.get("task_id") != self.id or not secrets.compare_digest(
            str(document.get("token", "")), self.token
        ):
            raise PmslError("运行任务身份不匹配，拒绝控制。")
        return document

    def write(self, filename: str, document: Dict[str, Any]) -> None:
        write_document(
            self.paths, self.directory / filename, dict(document, task_id=self.id, token=self.token)
        )

    def load_plan(self, digest: str) -> Tuple[LaunchPlan, Dict[str, Any]]:
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise PmslError("启动描述指纹无效。")
        actual = hashlib.sha256(
            self.paths.inside(self.directory / "launch.json").read_bytes()
        ).hexdigest()
        if not secrets.compare_digest(actual, digest):
            raise PmslError("启动描述已经改变，拒绝启动。")
        document = self.read("launch.json")
        if not isinstance(document.get("server_id"), str) or not isinstance(
            document.get("name"), str
        ):
            raise PmslError("启动描述缺少服务器身份或名称。")
        data = document.get("plan")
        if not isinstance(data, dict):
            raise PmslError("启动描述无效。")
        executable, cwd = data.get("executable"), data.get("cwd")
        arguments, environment = data.get("arguments"), data.get("environment")
        if (
            not isinstance(executable, str)
            or not Path(executable).is_file()
            or not isinstance(cwd, str)
        ):
            raise PmslError("启动描述的执行文件或目录无效。")
        if not self.paths.inside(cwd).is_dir():
            raise PmslError("服务器工作目录不存在。")
        if not isinstance(arguments, list) or not all(
            isinstance(arg, str) and "\x00" not in arg for arg in arguments
        ):
            raise PmslError("启动参数必须为文本列表。")
        if not isinstance(environment, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in environment.items()
        ):
            raise PmslError("进程环境必须为文本映射。")
        encoding = data.get("encoding")
        if (
            not isinstance(encoding, str)
            or type(data.get("external_console")) is not bool
            or type(document.get("save_log")) is not bool
        ):
            raise PmslError("启动描述的字段类型无效。")
        try:
            codecs.lookup(encoding)
        except LookupError as exc:
            raise PmslError("日志编码不受支持。") from exc
        return LaunchPlan(
            executable, tuple(arguments), cwd, dict(environment), encoding, data["external_console"]
        ), document

    def claim(self, digest: str) -> None:
        with self.paths.inside(self.directory / "claimed").open("xb") as claim:
            claim.write(digest.encode("ascii"))

    def publish(
        self, snapshot: RuntimeSnapshot, identity: Dict[str, object], ack: int, logs: LogSnapshot
    ) -> None:
        self.write("output.json", dict(revision=logs.revision, lines=logs.lines))
        self.write(
            "status.json",
            dict(asdict(snapshot), state=snapshot.state.value, identity=identity, ack=ack),
        )
