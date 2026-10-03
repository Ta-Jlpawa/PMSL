"""新服务器创建和移入回收区的可恢复事务；重命名只改显示资料。"""

import hashlib
import json
import os
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from pmsl.domain.creation import CreationSpec
from pmsl.domain.errors import StorageError, ValidationError
from pmsl.domain.models import ServerProfile
from pmsl.domain.validation import validate_legacy_name
from pmsl.infrastructure.catalog import JsonServerStore, profile_from_dict
from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.preparation import Preparer
from pmsl.infrastructure.server_layout import ServerLayout
from pmsl.infrastructure.storage import JsonStorage


class ServerOperations:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage, self.paths = storage, storage.paths
        self.store = JsonServerStore(storage)
        self.layout = ServerLayout(self.paths)

    def _unique(self, name: str, server_id: str = "") -> None:
        validate_legacy_name(name)
        if any(
            profile.name.casefold() == name.casefold() and profile.id != server_id
            for profile in self.store.list()
        ):
            raise ValidationError("目标服务器名称已存在。")

    def _editable(self) -> None:
        from pmsl.application.runtime import ServerRuntime

        self.storage._require_lock()
        ServerRuntime(self.paths).ensure_no_unconfirmed_tasks()
        if self.pending():
            raise StorageError("存在未完成服务器事务，请先运行 --recover-operations。")

    def commit_creation(self, spec: CreationSpec) -> ServerProfile:
        self._editable()
        self._unique(spec.name, spec.task_id)
        source = self.paths.data("staging/%s/server" % spec.task_id)
        destination = self.paths.data("servers/" + spec.task_id)
        task = self.storage.read("staging/%s/task.json" % spec.task_id)
        if (
            task.get("accepted") is not True
            or task.get("state") != "committing"
            or task.get("spec") != asdict(spec)
        ):
            raise StorageError("没有与创建输入匹配的明确 EULA 同意记录。")
        Preparer(self.paths).validate_generated(source, accepted=True)
        if not self.paths.inside(source / ".pmsl-launch.json").is_file():
            raise StorageError("缺少初始化成功的启动配方，不能提交服务器。")
        recipe = json.loads((source / ".pmsl-launch.json").read_text(encoding="utf-8"))
        if recipe.get("task_id") != spec.task_id or recipe.get("selection") != asdict(
            spec.selection
        ):
            raise StorageError("初始化配方与创建输入不匹配。")
        profile = ServerProfile(
            spec.task_id,
            spec.name,
            spec.selection,
            spec.memory_gib,
            self.paths.relative(destination),
        )
        profile_from_dict(asdict(profile), self.paths)
        marker = dict(schema_version=1, id=spec.task_id, selection=asdict(spec.selection))
        atomic_write(self.paths, source / ".pmsl-owner.json", json.dumps(marker).encode())
        recipe_digest = hashlib.sha256((source / ".pmsl-launch.json").read_bytes()).hexdigest()
        journal = dict(
            schema_version=1,
            kind="create",
            state="prepared",
            profile=asdict(profile),
            source=self.paths.relative(source),
            destination=self.paths.relative(destination),
            recipe_sha256=recipe_digest,
        )
        name = "operations/create-%s.json" % spec.task_id
        self.storage.write(name, journal)
        self._apply(name, journal)
        return profile

    def rename(self, server_id: str, name: str) -> ServerProfile:
        self._editable()
        self._unique(name, server_id)
        original = self.store.get(server_id)
        self.layout.validate(original)
        profile = replace(original, name=name)
        self.store.save(profile)
        return profile

    def trash(self, server_id: str) -> Path:
        self._editable()
        profile = self.store.get(server_id)
        source = self.layout.validate(profile)
        if source != self.paths.data("servers/" + server_id):
            raise StorageError("本批回收事务只处理稳定 ID 目录中的新服务器。")
        operation_id = uuid4().hex
        destination = self.paths.data("trash/" + operation_id + "/server")
        journal = dict(
            schema_version=1,
            kind="trash",
            state="prepared",
            profile=asdict(profile),
            source=self.paths.relative(source),
            destination=self.paths.relative(destination),
        )
        name = "operations/trash-%s.json" % operation_id
        self.storage.write(name, journal)
        self._apply(name, journal)
        return destination

    def list_trash(self) -> List[Dict[str, Any]]:
        result = []
        for path in sorted(self.paths.data("operations").glob("trash-*.json")):
            journal = self.storage.read("operations/" + path.name)
            if journal.get("kind") != "trash" or journal.get("state") != "committed":
                continue
            profile = profile_from_dict(journal["profile"], self.paths)
            self.layout.validate(profile, exists=False)
            operation_id = path.stem.removeprefix("trash-")
            if len(operation_id) != 32 or any(c not in "0123456789abcdef" for c in operation_id):
                raise StorageError("回收记录 ID 无效。")
            source = self.paths.data("trash/%s/server" % operation_id)
            if source.exists():
                self.layout.verify_owner(source, profile)
                result.append(dict(operation_id=operation_id, profile=asdict(profile)))
        return result

    def restore(self, operation_id: str) -> ServerProfile:
        self._editable()
        entry = next(
            (item for item in self.list_trash() if item["operation_id"] == operation_id), None
        )
        if entry is None:
            raise StorageError("没有找到可恢复的回收记录。")
        profile = profile_from_dict(entry["profile"], self.paths)
        self._unique(profile.name)
        destination = self.layout.directory(profile.id)
        if destination.exists() or any(item.id == profile.id for item in self.store.list()):
            raise StorageError("恢复目标已经存在，未覆盖服务器。")
        journal = dict(
            schema_version=1,
            kind="restore",
            state="prepared",
            profile=asdict(profile),
            source=self.paths.relative(self.paths.data("trash/%s/server" % operation_id)),
            destination=self.paths.relative(destination),
            trash_id=operation_id,
        )
        name = "operations/restore-%s.json" % uuid4().hex
        self.storage.write(name, journal)
        self._apply(name, journal)
        return profile

    def _apply(self, name: str, journal: Dict[str, Any]) -> None:
        self.storage._require_lock()
        profile = profile_from_dict(journal["profile"], self.paths)
        kind = journal.get("kind")
        source = self.paths.inside(journal["source"])
        destination = self.paths.inside(journal["destination"])
        if kind == "create":
            if (
                Path(name).name != "create-%s.json" % profile.id
                or source != self.paths.data("staging/%s/server" % profile.id)
                or destination != self.paths.data("servers/" + profile.id)
                or profile.directory != self.paths.relative(destination)
            ):
                raise StorageError("创建事务路径不匹配。")
        elif kind == "trash":
            operation_id = Path(name).stem.removeprefix("trash-")
            if (
                len(operation_id) != 32
                or any(character not in "0123456789abcdef" for character in operation_id)
                or source != self.paths.data("servers/" + profile.id)
                or profile.directory != self.paths.relative(source)
                or destination != self.paths.data("trash/%s/server" % operation_id)
            ):
                raise StorageError("回收事务路径不匹配。")
        elif kind == "restore":
            trash_id = journal.get("trash_id")
            if (
                not isinstance(trash_id, str)
                or len(trash_id) != 32
                or any(c not in "0123456789abcdef" for c in trash_id)
            ):
                raise StorageError("恢复事务回收 ID 无效。")
            if (
                source != self.paths.data("trash/%s/server" % trash_id)
                or destination != self.layout.directory(profile.id)
                or profile.directory != self.paths.relative(destination)
            ):
                raise StorageError("恢复事务路径不匹配。")
            original = self.storage.read("operations/trash-%s.json" % trash_id)
            if (
                original.get("state") != "committed"
                or original.get("profile") != asdict(profile)
                or original.get("destination") != journal["source"]
            ):
                raise StorageError("恢复事务与原回收记录不匹配。")
        else:
            raise StorageError("未知服务器事务类型。")
        existing = next((value for value in self.store.list() if value.id == profile.id), None)
        if existing is not None and existing != profile:
            raise StorageError("服务器事务与后来修改的资料冲突，未覆盖。")
        if source.exists() and destination.exists():
            raise StorageError("事务来源和目标同时存在，未覆盖任何文件。")
        current = source if source.is_dir() else destination
        if not current.is_dir():
            raise StorageError("事务的服务器目录缺失。")
        self.layout.validate(profile, exists=False)
        for entry in current.rglob("*"):
            self.paths.inside(entry)
        self.layout.verify_owner(current, profile)
        if kind == "restore":
            self._unique(profile.name, profile.id)
        if kind == "create":
            if hashlib.sha256(
                (current / ".pmsl-launch.json").read_bytes()
            ).hexdigest() != journal.get("recipe_sha256"):
                raise StorageError("事务启动配方已改变。")
            Preparer(self.paths).validate_generated(current, accepted=True)
            self._unique(profile.name, profile.id)
        if source.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.rename(str(self.paths.inside(source)), str(self.paths.inside(destination)))
        if kind in {"create", "restore"}:
            if existing is None:
                self.store.save(profile)
        elif existing is not None:
            self.store.remove(profile.id)
        self.storage.write(name, dict(journal, state="committed"))

    def pending(self) -> List[str]:
        directory = self.paths.data("operations")
        result = []
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                if not path.name.startswith(("create-", "trash-", "restore-")):
                    continue
                name = "operations/" + path.name
                document = self.storage.read(name)
                if document.get("kind") not in {"create", "trash", "restore"} or document.get(
                    "state"
                ) not in {
                    "prepared",
                    "committed",
                }:
                    raise StorageError("服务器事务类型或状态无效，请人工检查。")
                if document["state"] == "prepared":
                    result.append(name)
        return result

    def recover(self) -> int:
        from pmsl.application.runtime import ServerRuntime

        self.storage._require_lock()
        ServerRuntime(self.paths).ensure_no_unconfirmed_tasks()
        count = 0
        for name in self.pending():
            try:
                self._apply(name, self.storage.read(name))
            except (KeyError, ValueError, TypeError, OSError) as exc:
                raise StorageError("无法恢复服务器事务：%s" % name) from exc
            count += 1
        return count
