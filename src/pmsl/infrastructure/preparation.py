"""核心安装、未同意 EULA 的初始化以及可重用启动配方。"""

import json
import os
import re
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from pmsl.domain.creation import CreationSpec, ExecutionResult
from pmsl.domain.errors import PreparationError
from pmsl.domain.models import LaunchPlan
from pmsl.infrastructure.downloads import check_cancel, validate_jar
from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.java import JavaDetector, JavaInfo
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.process import ProcessSession
from pmsl.infrastructure.properties import PropertiesDocument

Executor = Callable[[LaunchPlan, threading.Event], ExecutionResult]


class Preparer:
    def __init__(self, paths: AppPaths, executor: Optional[Executor] = None) -> None:
        self.paths = paths
        self.executor = executor if executor is not None else self.execute

    def execute(self, plan: LaunchPlan, cancel: threading.Event) -> ExecutionResult:
        parent = self.paths.inside(plan.cwd).parent.name
        task_id = parent if re.fullmatch(r"[0-9a-f]{32}", parent) else uuid4().hex
        session = ProcessSession(self.paths, task_id, "creation", plan, save_log=True)
        try:
            session.start()
            deadline = time.monotonic() + 600
            while session.snapshot().active:
                if cancel.is_set():
                    session.force_stop()
                    check_cancel(cancel)
                if time.monotonic() > deadline:
                    session.force_stop()
                    raise PreparationError("核心初始化超过10分钟，已清理此任务进程树。")
                if session.snapshot().ready:
                    session.request_stop()
                cancel.wait(0.05)
            session.close()
            result = session.snapshot()
            return ExecutionResult(result.exit_code or 0, session.logs().lines)
        finally:
            session.close()

    def prepare(
        self, spec: CreationSpec, directory: Path, java: JavaInfo, cancel: threading.Event
    ) -> Dict[str, object]:
        directory = self.paths.inside(directory)
        artifact = self.paths.inside(directory / "core.jar")
        required = validate_jar(artifact, cancel)
        if required is not None and java.major < required:
            raise PreparationError(
                "所选核心入口至少需要 Java %d，当前为 Java %d。" % (required, java.major)
            )
        arguments: List[str] = ["-jar", "core.jar", "--nogui"]
        if spec.selection.core == "Forge":
            install = LaunchPlan(
                java.executable,
                (
                    "-Djava.io.tmpdir=" + str(self.paths.data("tmp")),
                    "-jar",
                    "core.jar",
                    "--installServer",
                ),
                str(directory),
            )
            result = self.executor(install, cancel)
            check_cancel(cancel)
            if result.exit_code != 0:
                raise PreparationError(
                    "Forge 安装失败（退出码 %d），未进入 EULA。" % result.exit_code
                )
            coordinate = spec.selection.minecraft_version + "-" + str(spec.selection.build)
            argument_file = (
                Path("libraries/net/minecraftforge/forge")
                / coordinate
                / ("win_args.txt" if os.name == "nt" else "unix_args.txt")
            )
            installed = self.paths.inside(directory / argument_file)
            if installed.is_file() and installed.stat().st_size > 0:
                arguments = ["@" + argument_file.as_posix(), "--nogui"]
            else:
                old_jar = self.paths.inside(directory / ("forge-" + coordinate + ".jar"))
                if not old_jar.is_file():
                    raise PreparationError("Forge 安装缺少所选版本的启动参数或服务器 JAR。")
                validate_jar(old_jar, cancel)
                arguments = ["-jar", old_jar.name, "--nogui"]
        # 重试只能继续未同意的初始化，不因残留 eula=true 启动完整世界。
        eula_path = self.paths.inside(directory / "eula.txt")
        if eula_path.exists():
            document = PropertiesDocument.read(self.paths, eula_path)
            if document.get("eula") == "true":
                document.set("eula", "false")
                document.save(self.paths, eula_path)
        plan = LaunchPlan(
            java.executable,
            tuple(
                [
                    "-Dfile.encoding=UTF-8",
                    "-Dstdout.encoding=UTF-8",
                    "-Dstderr.encoding=UTF-8",
                    "-Djava.io.tmpdir=" + str(self.paths.data("tmp")),
                    "-Xms%dG" % spec.memory_gib,
                    "-Xmx%dG" % spec.memory_gib,
                ]
                + arguments
            ),
            str(directory),
        )
        result = self.executor(plan, cancel)
        check_cancel(cancel)
        self.validate_generated(directory, accepted=False)
        expected_eula = any(
            "eula" in line.lower()
            and any(word in line.lower() for word in ("agree", "accept", "同意"))
            for line in result.lines
        )
        if result.exit_code != 0 and not expected_eula:
            raise PreparationError(
                "服务器初始化失败（退出码 %d），未确认预期的 EULA 退出。" % result.exit_code
            )
        recipe: Dict[str, object] = dict(
            schema_version=1,
            task_id=spec.task_id,
            selection=asdict(spec.selection),
            arguments=arguments,
            java_min=required,
        )
        atomic_write(
            self.paths,
            directory / ".pmsl-launch.json",
            json.dumps(recipe, ensure_ascii=False).encode("utf-8"),
        )
        return recipe

    def validate_generated(self, directory: Path, accepted: bool) -> None:
        directory = self.paths.inside(directory)
        for path in directory.rglob("*"):
            self.paths.inside(path)
        try:
            eula = PropertiesDocument.read(self.paths, directory / "eula.txt")
            properties = PropertiesDocument.read(self.paths, directory / "server.properties")
        except OSError as exc:
            raise PreparationError(
                "初始化缺少 EULA 或服务器配置，请检查程序内的任务日志。"
            ) from exc
        if eula.get("eula") != ("true" if accepted else "false") or not properties.values():
            raise PreparationError("初始化没有生成有效的 EULA 和服务器属性，不能强制继续。")


def profile_launch_plan(
    paths: AppPaths, directory: str, memory: int, configured_java: Optional[str], external: bool
) -> LaunchPlan:
    root = paths.inside(directory)
    try:
        recipe = json.loads(paths.inside(root / ".pmsl-launch.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PreparationError("新服务器启动配方缺失或损坏。") from exc
    arguments = recipe.get("arguments")
    if (
        recipe.get("schema_version") != 1
        or not isinstance(arguments, list)
        or not arguments
        or not all(isinstance(value, str) for value in arguments)
    ):
        raise PreparationError("服务器启动配方格式无效。")
    # 配方只能指向本服务器目录里的核心或安装参数文件。
    if arguments[-1] != "--nogui":
        raise PreparationError("服务器启动配方参数不受支持。")
    targets = (
        [arguments[1]]
        if len(arguments) == 3 and arguments[0] == "-jar"
        else [arguments[0][1:]]
        if len(arguments) == 2 and arguments[0].startswith("@")
        else []
    )
    if not targets:
        raise PreparationError("服务器启动配方参数不受支持。")
    for value in targets:
        target = paths.inside(root / value)
        if not target.is_file() or root not in target.parents:
            raise PreparationError("服务器启动配方指向无效文件。")
    java = JavaDetector(paths).detect(configured_java)
    required = recipe.get("java_min")
    if required is not None and (type(required) is not int or java.major < required):
        raise PreparationError("当前 Java 不满足服务器入口要求。")
    temporary = paths.data("tmp")
    return LaunchPlan(
        java.executable,
        tuple(
            [
                "-Dfile.encoding=UTF-8",
                "-Dstdout.encoding=UTF-8",
                "-Dstderr.encoding=UTF-8",
                "-Djava.io.tmpdir=" + str(temporary),
                "-Xms%dG" % memory,
                "-Xmx%dG" % memory,
            ]
            + arguments
        ),
        str(root),
        external_console=external,
    )
