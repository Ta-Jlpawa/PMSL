"""所有持久化文件限定在程序目录，拒绝符号链接和重解析点。"""

import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from pmsl.domain.errors import StorageError, UnsafePathError

PathValue = Union[str, Path]


@dataclass(frozen=True)
class AppPaths:
    program_dir: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "program_dir", self.program_dir.resolve(strict=True))

    @classmethod
    def discover(cls) -> "AppPaths":
        if getattr(sys, "frozen", False):
            return cls(Path(sys.executable).resolve().parent)
        # 源码布局是 <程序目录>/src/pmsl/infrastructure/paths.py。
        return cls(Path(__file__).resolve().parents[3])

    def inside(self, value: PathValue) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.program_dir / candidate
        candidate = Path(os.path.abspath(candidate))
        try:
            relative = candidate.relative_to(self.program_dir)
        except ValueError as exc:
            raise UnsafePathError("路径必须位于程序目录内：%s" % candidate) from exc
        current = self.program_dir
        for part in relative.parts:
            current = current / part
            try:
                attributes = current.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(attributes.st_mode) or (
                getattr(attributes, "st_file_attributes", 0) & 0x400
            ):
                raise UnsafePathError("程序数据路径不能经过链接或重解析点：%s" % current)
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.program_dir)
        except ValueError as exc:
            raise UnsafePathError("解析后的路径越出程序目录：%s" % resolved) from exc
        return resolved

    @property
    def data_dir(self) -> Path:
        return self.inside(".pmsl")

    def bundled(self, relative: PathValue) -> Path:
        directory = self.program_dir
        if getattr(sys, "frozen", False):
            directory = self.inside(Path(getattr(sys, "_MEIPASS", directory)))
        path = self.inside(directory / relative)
        try:
            path.relative_to(directory)
        except ValueError as exc:
            raise UnsafePathError("打包资源路径越出程序资源目录：%s" % path) from exc
        return path

    def data(self, relative: PathValue) -> Path:
        path = self.inside(self.data_dir / relative)
        try:
            path.relative_to(self.data_dir)
        except ValueError as exc:
            raise UnsafePathError("新数据路径越出 .pmsl：%s" % path) from exc
        return path

    def resource(self, relative: PathValue) -> Path:
        directory = self.bundled("data")
        path = self.inside(directory / relative)
        try:
            path.relative_to(directory)
        except ValueError as exc:
            raise UnsafePathError("资源路径越出 data：%s" % path) from exc
        return path

    def relative(self, value: PathValue) -> str:
        return self.inside(value).relative_to(self.program_dir).as_posix()

    def initialize(self) -> None:
        try:
            for directory in (
                "servers",
                "user-assets",
                "cache/catalogs",
                "cache/downloads",
                "staging",
                "runtime",
                "logs",
                "backups",
                "trash",
                "operations",
                "tmp",
            ):
                self.data(directory).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError("程序目录不可写，请将完整程序放入可写目录。") from exc
