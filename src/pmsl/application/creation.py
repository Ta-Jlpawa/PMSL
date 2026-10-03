"""
创建后台任务
用于发布快照，不接触界面、弹窗或目录清单。
"""

import json
import re
import threading
from dataclasses import asdict, replace
from typing import Any, Callable, Dict, List, Optional, Tuple

from pmsl.domain.creation import CreationSnapshot, CreationSpec
from pmsl.domain.errors import PmslError, TaskCancelled, ValidationError
from pmsl.domain.models import CoreSelection
from pmsl.domain.states import CreationState
from pmsl.domain.validation import positive_integer, validate_legacy_name
from pmsl.infrastructure.downloads import Downloader, check_cancel, validate_jar
from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.java import JavaDetector
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.preparation import Preparer
from pmsl.infrastructure.properties import PropertiesDocument
from pmsl.infrastructure.providers import CoreProviders
from pmsl.infrastructure.storage import JsonStorage


class CreationTask:
    def __init__(
        self,
        paths: AppPaths,
        spec: CreationSpec,
        providers: CoreProviders,
        downloader: Downloader,
        preparer: Preparer,
    ) -> None:
        if re.fullmatch(r"[0-9a-f]{32}", spec.task_id) is None:
            raise ValidationError("创建任务 ID 无效。")
        validate_legacy_name(spec.name)
        positive_integer(spec.memory_gib, "运行内存")
        self.paths, self.spec = paths, spec
        self.providers, self.downloader, self.preparer = providers, downloader, preparer
        self.directory = paths.data("staging/" + spec.task_id)
        self.server_dir = paths.inside(self.directory / "server")
        self.cancelled = threading.Event()
        self._lock = threading.Lock()
        self._snapshot = CreationSnapshot(spec.task_id, CreationState.EDITING)
        self._thread: Optional[threading.Thread] = None
        self.accepted = False
        self.artifact_sha256: Optional[str] = None
        self.recipe_sha256: Optional[str] = None

    @property
    def busy(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def snapshot(self) -> CreationSnapshot:
        with self._lock:
            return self._snapshot

    def _state(self, state: CreationState, error: Optional[str] = None) -> None:
        with self._lock:
            self._snapshot = replace(self._snapshot, state=state, error=error)
            document = dict(
                schema_version=1,
                spec=asdict(self.spec),
                state=state.value,
                error=error,
                accepted=self.accepted,
                artifact_sha256=self.artifact_sha256,
                recipe_sha256=self.recipe_sha256,
            )
        atomic_write(
            self.paths,
            self.directory / "task.json",
            json.dumps(document, ensure_ascii=False).encode("utf-8"),
        )

    def _launch(self, state: CreationState, worker: Callable[[], None]) -> None:
        if self.busy or self.snapshot().state in {
            CreationState.COMMITTING,
            CreationState.COMPLETED,
        }:
            raise PmslError("创建任务尚未释放资源，不能重新开始。")
        self.cancelled.clear()
        self._state(state)

        def run() -> None:
            try:
                worker()
            except TaskCancelled:
                self._state(CreationState.CANCELLED)
            except Exception as exc:
                # 工作线程的最终出口必须可靠发布错误，避免未知异常留下运行假象。
                self._state(CreationState.FAILED, str(exc))

        self._thread = threading.Thread(target=run, name="pmsl-creation", daemon=False)
        self._thread.start()

    def download(self) -> None:
        def work() -> None:
            artifact = self.providers.resolve(self.spec.selection, self.cancelled)
            with self._lock:
                self._snapshot = replace(
                    self._snapshot,
                    source=artifact.source,
                    verified_upstream=artifact.sha256 is not None,
                )

            def progress(received: int, total: Optional[int]) -> None:
                with self._lock:
                    self._snapshot = replace(self._snapshot, received=received, total=total)

            cached = self.downloader.fetch(artifact, self.cancelled, progress)
            self.server_dir.mkdir(parents=True, exist_ok=True)
            partial = self.paths.inside(self.server_dir / "core.jar.part")
            try:
                with cached.open("rb") as source, partial.open("wb") as target:
                    while True:
                        check_cancel(self.cancelled)
                        block = source.read(65536)
                        if not block:
                            break
                        target.write(block)
                check_cancel(self.cancelled)
                partial.replace(self.paths.inside(self.server_dir / "core.jar"))
            finally:
                if partial.exists():
                    partial.unlink()
            self.artifact_sha256 = Downloader._digest(self.server_dir / "core.jar", self.cancelled)
            self.recipe_sha256 = None
            self._state(CreationState.DOWNLOADED)

        self._launch(CreationState.DOWNLOADING, work)

    def prepare(self, configured_java: Optional[str]) -> None:
        if (
            self.snapshot().state
            not in {CreationState.DOWNLOADED, CreationState.FAILED, CreationState.CANCELLED}
            or not self.paths.inside(self.server_dir / "core.jar").is_file()
        ):
            raise PmslError("核心尚未下载完成，不能开始初始化。")

        def work() -> None:
            java = JavaDetector(self.paths).detect(configured_java)
            self.preparer.prepare(self.spec, self.server_dir, java, self.cancelled)
            check_cancel(self.cancelled)
            self.recipe_sha256 = Downloader._digest(
                self.server_dir / ".pmsl-launch.json", self.cancelled
            )
            self._state(CreationState.WAITING_FOR_EULA)

        self._launch(CreationState.PREPARING, work)

    def accept_eula(self) -> None:
        if self.accepted and self.snapshot().state is CreationState.COMMITTING and not self.busy:
            self.preparer.validate_generated(self.server_dir, accepted=True)
            return
        if self.busy or self.snapshot().state is not CreationState.WAITING_FOR_EULA:
            raise PmslError("初始化没有成功完成，不能同意 EULA 或提交。")
        self.preparer.validate_generated(self.server_dir, accepted=False)
        document = PropertiesDocument.read(self.paths, self.server_dir / "eula.txt")
        document.set("eula", "true")
        document.save(self.paths, self.server_dir / "eula.txt")
        self.accepted = True
        self._state(CreationState.COMMITTING)

    def mark_completed(self) -> None:
        self._state(CreationState.COMPLETED)

    @staticmethod
    def pending(storage: JsonStorage) -> List[Tuple[str, Dict[str, Any]]]:
        from pmsl.infrastructure.catalog import JsonServerStore

        committed = {profile.id for profile in JsonServerStore(storage).list()}
        result = []
        entries = storage.paths.data("staging").glob("*/task.json")
        for path in sorted(
            entries, key=lambda item: storage.paths.inside(item).stat().st_mtime, reverse=True
        ):
            task_id = path.parent.name
            if re.fullmatch(r"[0-9a-f]{32}", task_id) is None:
                raise ValidationError("创建目录名称不是有效任务 ID。")
            document = storage.read("staging/%s/task.json" % task_id)
            if document.get("state") != CreationState.COMPLETED.value and task_id not in committed:
                result.append((task_id, document))
        return result

    @classmethod
    def restore(
        cls,
        storage: JsonStorage,
        task_id: str,
        providers: CoreProviders,
        downloader: Downloader,
        preparer: Preparer,
    ) -> "CreationTask":
        storage._require_lock()
        if re.fullmatch(r"[0-9a-f]{32}", task_id) is None:
            raise ValidationError("创建任务 ID 无效。")
        document = storage.read("staging/%s/task.json" % task_id)
        try:
            raw = document["spec"]
            spec = CreationSpec(**dict(raw, selection=CoreSelection(**raw["selection"])))
            if spec.task_id != task_id or spec.selection.core not in {
                "Paper",
                "Spigot",
                "Forge",
                "Fabric",
            }:
                raise ValidationError("创建任务输入身份不匹配。")
            state = CreationState(document["state"])
            if type(document["accepted"]) is not bool:
                raise ValidationError("创建任务同意标志无效。")
            if document["accepted"] and state not in {
                CreationState.COMMITTING,
                CreationState.COMPLETED,
            }:
                raise ValidationError("创建任务同意状态不一致。")
            task = cls(storage.paths, spec, providers, downloader, preparer)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError("创建任务记录损坏，未自动修复。") from exc
        if state is CreationState.COMPLETED:
            raise PmslError("此创建任务已经完成。")
        task.artifact_sha256 = document.get("artifact_sha256")
        task.recipe_sha256 = document.get("recipe_sha256")
        core = task.paths.inside(task.server_dir / "core.jar")
        if task.artifact_sha256 is None or not core.is_file():
            if state in {CreationState.WAITING_FOR_EULA, CreationState.COMMITTING}:
                raise PmslError("创建任务的核心校验记录缺失，不能继续提交。")
            task._state(CreationState.FAILED, "上次下载未完成，请重新下载。")
            return task
        if Downloader._digest(core, task.cancelled) != task.artifact_sha256:
            raise PmslError("创建任务核心已改变，拒绝继续。")
        validate_jar(core, task.cancelled)
        if state in {CreationState.WAITING_FOR_EULA, CreationState.COMMITTING}:
            recipe_path = task.paths.inside(task.server_dir / ".pmsl-launch.json")
            if (
                not recipe_path.is_file()
                or Downloader._digest(recipe_path, task.cancelled) != task.recipe_sha256
            ):
                raise PmslError("创建任务启动配方已改变，拒绝继续。")
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            if recipe.get("task_id") != task_id or recipe.get("selection") != asdict(
                spec.selection
            ):
                raise PmslError("创建任务的配方不属于所选核心。")
            task.accepted = document["accepted"]
            if state is CreationState.COMMITTING and not task.accepted:
                raise PmslError("缺少明确的 EULA 同意记录。")
            if not task.accepted:
                eula_path = task.paths.inside(task.server_dir / "eula.txt")
                eula = PropertiesDocument.read(task.paths, eula_path)
                if eula.get("eula") == "true":
                    eula.set("eula", "false")
                    eula.save(task.paths, eula_path)
            preparer.validate_generated(task.server_dir, accepted=task.accepted)
            task._state(state)
        else:
            # 初始化中断只回到已下载状态，由用户再次启动准备流程。
            task.recipe_sha256 = None
            task._state(CreationState.DOWNLOADED)
        return task

    def cancel(self) -> None:
        if self.busy:
            self.cancelled.set()

    def close(self) -> None:
        self.cancel()
        if self._thread is not None:
            self._thread.join(timeout=15)
            if self._thread.is_alive():
                raise PmslError("创建任务仍在释放连接，不能退出程序。")
