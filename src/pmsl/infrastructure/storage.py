"""提供跨进程实例锁、JSON 原子读写、备份和损坏文件恢复。"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Callable, Dict, Optional

from pmsl.domain.errors import (
    InstanceRunningError,
    StorageError,
    UnsupportedSchemaError,
)
from pmsl.domain.models import SCHEMA_VERSION
from pmsl.infrastructure.paths import AppPaths

Document = Dict[str, Any]


def validate_schema(document: Document) -> None:
    if not isinstance(document, dict):
        raise StorageError("数据文件顶层必须为对象。")
    version = document.get("schema_version")
    if type(version) is not int:
        raise StorageError("数据文件缺少有效的 schema_version。")
    if version != SCHEMA_VERSION:
        raise UnsupportedSchemaError("不支持的数据版本 %s，拒绝覆盖。" % version)


class InstanceLock:
    """通过操作系统文件锁限制同一程序目录的并发写入，退出时释放锁。"""

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        self._file: Optional[BinaryIO] = None

    @property
    def held(self) -> bool:
        return self._file is not None

    def __enter__(self) -> "InstanceLock":
        if self.held:
            raise InstanceRunningError("当前锁已经被获取。")
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        handle = self.paths.data("instance.lock").open("a+b")
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            raise InstanceRunningError("已有实例正在管理此程序目录。") from exc
        self._file = handle
        return self

    def __exit__(self, *args: object) -> None:
        handle = self._file
        if handle is None:
            return
        try:
            handle.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._file = None
            handle.close()


class JsonStorage:
    """读写程序数据目录中的 JSON；修改操作要求持有对应的实例锁。"""

    def __init__(self, paths: AppPaths, lock: Optional[InstanceLock] = None) -> None:
        if lock is not None and lock.paths != paths:
            raise StorageError("写锁不属于此程序目录。")
        self.paths = paths
        self.lock = lock

    def _require_lock(self) -> None:
        if self.lock is None or not self.lock.held:
            raise StorageError("修改数据前必须获取实例锁。")

    def read(
        self, relative: str, validator: Callable[[Document], None] = validate_schema
    ) -> Document:
        path = self.paths.data(relative)
        try:
            with path.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
            if not isinstance(document, dict):
                raise StorageError("JSON 顶层必须为对象：%s" % path)
            validator(document)
            return document
        except (OSError, UnicodeError, ValueError) as exc:
            raise StorageError("无法读取 %s：%s" % (path, exc)) from exc

    def _replace_bytes(self, path: Path, content: bytes) -> None:
        self._require_lock()
        path = self.paths.inside(path)
        temporary: Optional[Path] = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # 在目标目录创建暂存文件，确保后续替换位于同一文件系统。
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=".%s-" % path.name,
                suffix=".tmp",
                dir=str(path.parent),
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            self.paths.inside(path)
            os.replace(str(temporary), str(path))
        except OSError as exc:
            raise StorageError("无法写入 %s：%s" % (path, exc)) from exc
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def write(
        self,
        relative: str,
        document: Document,
        validator: Callable[[Document], None] = validate_schema,
    ) -> None:
        self._require_lock()
        validator(document)
        path = self.paths.data(relative)
        try:
            payload = (
                json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise StorageError("数据包含无法保存的 JSON 值。") from exc
        if path.exists():
            previous = self.read(relative, validator)
            backup = (json.dumps(previous, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            self._replace_bytes(self.paths.data(relative + ".bak"), backup)
        self._replace_bytes(path, payload)

    def backup_source(self, relative: str, payload: bytes) -> None:
        path = self.paths.data(Path("backups") / relative)
        if path.exists():
            if path.read_bytes() != payload:
                raise StorageError("迁移备份与源文件不一致，拒绝覆盖：%s" % path)
            return
        self._replace_bytes(path, payload)

    def recover_backup(
        self,
        relative: str,
        validator: Callable[[Document], None] = validate_schema,
    ) -> None:
        """用有效备份恢复缺失或损坏的文件；不覆盖有效文件或不支持的数据版本。"""
        self._require_lock()
        primary = self.paths.data(relative)
        if primary.exists():
            try:
                self.read(relative, validator)
            except UnsupportedSchemaError:
                raise
            except StorageError:
                pass
            else:
                raise StorageError("主文件有效，无需恢复备份。")
        backup = self.read(relative + ".bak", validator)
        if primary.exists():
            # 恢复前另存损坏文件，保留原始内容供排查。
            self._replace_bytes(self.paths.data(relative + ".damaged"), primary.read_bytes())
        content = (json.dumps(backup, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self._replace_bytes(primary, content)
