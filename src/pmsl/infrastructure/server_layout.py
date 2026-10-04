"""按服务器 ID 定位目录，并校验目录归属和服务器身份。"""

import json
import re
from dataclasses import asdict
from pathlib import Path

from pmsl.domain.errors import StorageError
from pmsl.domain.models import ServerProfile
from pmsl.infrastructure.paths import AppPaths


class ServerLayout:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def directory(self, server_id: str) -> Path:
        if not isinstance(server_id, str) or re.fullmatch(r"[0-9a-f]{32}", server_id) is None:
            raise StorageError("服务器 ID 无效。")
        return self.paths.data("servers/" + server_id)

    def validate(self, profile: ServerProfile, *, exists: bool = True) -> Path:
        root = self.directory(profile.id)
        if (
            profile.directory != self.paths.relative(root)
            or profile.legacy_name is not None
            or profile.legacy_launch_script is not None
        ):
            raise StorageError("新界面只管理 .pmsl/servers/<id> 中的服务器。")
        if profile.icon not in {None, self.paths.relative(root / "icon.png")}:
            raise StorageError("服务器图标必须保存在其自身的 icon.png。")
        if exists:
            self.verify_owner(root, profile)
        return root

    def verify_owner(self, root: Path, profile: ServerProfile) -> None:
        root = self.paths.inside(root)
        if not root.is_dir():
            raise StorageError("服务器目录不存在：%s" % profile.name)
        try:
            marker = json.loads(
                self.paths.inside(root / ".pmsl-owner.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise StorageError("服务器目录身份文件缺失或损坏。") from exc
        if (
            not isinstance(marker, dict)
            or type(marker.get("schema_version")) is not int
            or marker.get("schema_version") != 1
            or marker.get("id") != profile.id
            or marker.get("selection") != asdict(profile.selection)
        ):
            raise StorageError("服务器目录身份与清单不一致，已停止操作。")

    def file(self, profile: ServerProfile, relative: str) -> Path:
        root = self.validate(profile)
        target = self.paths.inside(root / relative)
        if root not in target.parents:
            raise StorageError("服务器文件不能越出自身目录。")
        return target
