"""自定义资源复制到程序内独立目录，失败时只清理本次副本。"""

import os
from pathlib import Path
from typing import Callable
from uuid import uuid4

from pmsl.domain.errors import StorageError
from pmsl.infrastructure.storage import JsonStorage

MAX_ASSET_BYTES = 50 * 1024 * 1024


class UserAssets:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage, self.paths = storage, storage.paths

    def import_file(self, source: str, extension: str, validate: Callable[[Path], None]) -> str:
        self.storage._require_lock()
        origin = Path(source)
        if origin.suffix.lower() != extension or extension not in {".png", ".ttf"}:
            raise StorageError("请选择 PNG 图片或 TTF 字体。")
        # 文件名保留供界面显示；每次导入使用独立目录，避免同名资源覆盖。
        directory = self.paths.data("user-assets/" + uuid4().hex)
        target = self.paths.inside(directory / origin.name)
        partial = self.paths.inside(directory / "import.part")
        directory.mkdir(parents=True)
        try:
            received = 0
            with origin.open("rb") as incoming, partial.open("xb") as outgoing:
                while True:
                    block = incoming.read(65536)
                    if not block:
                        break
                    received += len(block)
                    if received > MAX_ASSET_BYTES:
                        raise StorageError("自定义资源不能超过 50 MiB。")
                    outgoing.write(block)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            validate(partial)
            os.replace(str(partial), str(target))
            return self.paths.relative(target)
        except BaseException:
            for path in (partial, target):
                if path.exists():
                    path.unlink()
            directory.rmdir()
            raise

    def discard(self, relative: str) -> None:
        self.storage._require_lock()
        target = self.paths.inside(relative)
        root = self.paths.data("user-assets")
        if target.parent.parent != root or len(target.parent.name) != 32:
            raise StorageError("只能清理本次导入的独立资源副本。")
        target.unlink()
        target.parent.rmdir()
