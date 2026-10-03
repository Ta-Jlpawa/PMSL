"""目录与设置的类型转换、版本验证和原子存储。"""

import re
from dataclasses import asdict
from typing import Any, Dict, List

from pmsl.domain.errors import StorageError, ValidationError
from pmsl.domain.models import AppSettings, CoreSelection, ServerProfile
from pmsl.domain.validation import positive_integer, validate_name
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.storage import Document, JsonStorage, validate_schema


def profile_from_dict(raw: Dict[str, Any], paths: AppPaths) -> ServerProfile:
    try:
        validate_schema(raw)
        profile = ServerProfile(**dict(raw, selection=CoreSelection(**raw["selection"])))
        if not re.fullmatch(r"[0-9a-f]{32}", profile.id):
            raise ValidationError("服务器 ID 必须为 32 位十六进制。")
        validate_name(profile.name)
        positive_integer(profile.memory_gib, "运行内存")
        if not isinstance(profile.directory, str) or not profile.directory:
            raise ValidationError("服务器目录不能为空。")
        if (
            not isinstance(profile.selection.minecraft_version, str)
            or not profile.selection.minecraft_version
        ):
            raise ValidationError("Minecraft 版本不能为空。")
        if profile.selection.core not in {"Paper", "Spigot", "Fabric", "Forge"}:
            raise ValidationError("不支持的核心：%s" % profile.selection.core)
        for value in asdict(profile.selection).values():
            if value is not None and (not isinstance(value, str) or not value):
                raise ValidationError("核心版本必须为非空字符串。")
        for value in (profile.directory, profile.icon):
            if value is not None:
                if not isinstance(value, str) or not value:
                    raise ValidationError("文件路径必须为非空字符串。")
                paths.inside(value)
        if profile.legacy_launch_script not in {None, "begin.bat", "run.bat"}:
            raise ValidationError("旧启动脚本只能记录为 begin.bat 或 run.bat。")
        if profile.java is not None and not isinstance(profile.java, str):
            raise ValidationError("Java 选择必须为字符串或 null。")
        return profile
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise StorageError("服务器资料格式错误：%s" % exc) from exc


def settings_from_dict(raw: Document, paths: AppPaths) -> AppSettings:
    validate_schema(raw)
    try:
        settings = AppSettings(**raw)
        if type(settings.fps) is not int or settings.fps not in (30, 60):
            raise ValidationError("帧率必须为 30 或 60。")
        for key in (
            "dynamic_background",
            "external_console",
            "save_server_log",
            "console_read_fix",
        ):
            if type(getattr(settings, key)) is not bool:
                raise ValidationError("设置 %s 必须为布尔值。" % key)
        for key in ("console_font", "console_background", "background", "loading_image"):
            value = getattr(settings, key)
            if value is not None:
                if not isinstance(value, str) or not value:
                    raise ValidationError("资源路径必须为非空字符串。")
                paths.inside(value)
        if settings.java is not None and (
            not isinstance(settings.java, str) or not settings.java.strip() or "\0" in settings.java
        ):
            raise ValidationError("Java 选择必须为非空路径字符串或 null。")
        if not isinstance(settings.legacy_options, dict):
            raise ValidationError("旧设置快照必须为对象。")
        return settings
    except (TypeError, ValueError, ValidationError) as exc:
        raise StorageError("程序设置格式错误：%s" % exc) from exc


class JsonServerStore:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def validate(self, document: Document) -> None:
        validate_schema(document)
        if not isinstance(document.get("servers"), list):
            raise StorageError("目录缺少服务器列表。")
        ids = set()
        for raw in document["servers"]:
            if not isinstance(raw, dict):
                raise StorageError("服务器资料必须为对象。")
            profile = profile_from_dict(raw, self.storage.paths)
            if profile.id in ids:
                raise StorageError("目录包含重复服务器 ID。")
            ids.add(profile.id)
        if not isinstance(document.get("migrations", {}), dict):
            raise StorageError("迁移映射必须为对象。")

    def document(self) -> Document:
        if not self.storage.paths.data("catalog.json").exists():
            return {"schema_version": 1, "servers": [], "migrations": {}}
        return self.storage.read("catalog.json", self.validate)

    def list(self) -> List[ServerProfile]:
        return [profile_from_dict(raw, self.storage.paths) for raw in self.document()["servers"]]

    def get(self, server_id: str) -> ServerProfile:
        for profile in self.list():
            if profile.id == server_id:
                return profile
        raise StorageError("未找到服务器：%s" % server_id)

    def save(self, profile: ServerProfile) -> None:
        raw = asdict(profile)
        profile_from_dict(raw, self.storage.paths)
        document = self.document()
        for index, item in enumerate(document["servers"]):
            if item["id"] == profile.id:
                document["servers"][index] = raw
                break
        else:
            document["servers"].append(raw)
        self.storage.write("catalog.json", document, self.validate)

    def remove(self, server_id: str) -> None:
        document = self.document()
        self.get(server_id)
        document["servers"] = [raw for raw in document["servers"] if raw["id"] != server_id]
        self.storage.write("catalog.json", document, self.validate)


class JsonSettingsStore:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def validate(self, document: Document) -> None:
        settings_from_dict(document, self.storage.paths)

    def load(self) -> AppSettings:
        if not self.storage.paths.data("settings.json").exists():
            return AppSettings()
        return settings_from_dict(
            self.storage.read("settings.json", self.validate), self.storage.paths
        )

    def save(self, settings: AppSettings) -> None:
        self.storage.write("settings.json", asdict(settings), self.validate)
