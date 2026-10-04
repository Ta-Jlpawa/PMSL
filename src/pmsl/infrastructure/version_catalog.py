"""读取和导入结构化版本目录与下载来源配置。"""

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

from pmsl.domain.errors import StorageError, ValidationError
from pmsl.domain.versions import (
    SUPPORTED_CORES,
    CoreBuild,
    GameRelease,
    VersionCatalog,
    validate_version,
)
from pmsl.infrastructure.providers import validate_template
from pmsl.infrastructure.storage import Document, JsonStorage, validate_schema


def catalog_from_dict(raw: Document) -> VersionCatalog:
    validate_schema(raw)
    try:
        if not isinstance(raw["games"], list) or not isinstance(raw["fabric"], dict):
            raise ValidationError("版本目录缺少游戏列表或 Fabric 版本。")
        games = []
        identities = set()
        for item in raw["games"]:
            core, version = item["core"], validate_version(item["version"])
            if core not in SUPPORTED_CORES or (core, version) in identities:
                raise ValidationError("核心无效或游戏版本重复。")
            identities.add((core, version))
            if not isinstance(item["builds"], list):
                raise ValidationError("构建列表必须为数组。")
            builds: List[CoreBuild] = []
            for build in item["builds"]:
                number = validate_version(build["version"])
                code = build.get("paper_code")
                if code is not None and (
                    core != "Paper"
                    or not isinstance(code, str)
                    or re.fullmatch("[0-9a-f]{64}", code) is None
                ):
                    raise ValidationError("Paper 对象代码必须为该构建的 64 位十六进制值。")
                if any(existing.version == number for existing in builds):
                    raise ValidationError("构建号重复。")
                builds.append(CoreBuild(number, code))
            if bool(builds) != (core in {"Paper", "Forge"}):
                raise ValidationError("Paper/Forge 必须提供构建，Spigot/Fabric 不使用构建列表。")
            games.append(GameRelease(core, version, tuple(builds)))

        def tokens(key: str) -> tuple:
            values = raw["fabric"][key]
            if not isinstance(values, list) or not values:
                raise ValidationError("Fabric 版本列表不能为空。")
            for value in values:
                validate_version(value)
            if len(set(values)) != len(values):
                raise ValidationError("Fabric 版本列表包含重复项。")
            return tuple(values)

        catalog = VersionCatalog(tuple(games), tokens("loaders"), tokens("installers"))
        if any(not catalog.versions(core) for core in SUPPORTED_CORES):
            raise ValidationError("目录必须包含四类受支持核心。")
        return catalog
    except (KeyError, TypeError, AttributeError, ValueError, ValidationError) as exc:
        raise StorageError("版本目录格式错误：%s" % exc) from exc


def catalog_document(catalog: VersionCatalog) -> Document:
    return dict(
        schema_version=1,
        games=[
            dict(
                core=game.core,
                version=game.version,
                builds=[asdict(build) for build in game.builds],
            )
            for game in catalog.games
        ],
        fabric=dict(
            loaders=list(catalog.fabric_loaders), installers=list(catalog.fabric_installers)
        ),
    )


class VersionCatalogStore:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage, self.paths = storage, storage.paths

    def validate(self, document: Document) -> None:
        catalog_from_dict(document)

    def _bundled(self, name: str) -> Document:
        return self.read_file(self.paths.resource("catalogs/" + name))

    @staticmethod
    def read_file(path: Path) -> Document:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            validate_schema(document)
            return document
        except (OSError, ValueError, UnicodeError) as exc:
            raise StorageError("无法读取结构化目录：%s" % path) from exc

    def load(self) -> VersionCatalog:
        name = "cache/catalogs/versions.json"
        raw = (
            self.storage.read(name, self.validate)
            if self.paths.data(name).exists()
            else self._bundled("versions.json")
        )
        return catalog_from_dict(raw)

    def import_file(self, path: str) -> VersionCatalog:
        self.storage._require_lock()
        catalog = catalog_from_dict(self.read_file(self.paths.inside(path)))
        self.storage.write("cache/catalogs/versions.json", catalog_document(catalog), self.validate)
        return catalog


class DownloadSourcesStore:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage, self.paths = storage, storage.paths

    def validate(self, document: Document) -> None:
        validate_schema(document)
        templates = document.get("templates")
        if not isinstance(templates, dict):
            raise StorageError("下载来源 templates 必须为对象。")
        for core, template in templates.items():
            validate_template(core, template)

    def load(self) -> Dict[str, str]:
        name = "download-sources.json"
        raw = (
            self.storage.read(name, self.validate)
            if self.paths.data(name).exists()
            else VersionCatalogStore.read_file(self.paths.resource("catalogs/" + name))
        )
        self.validate(raw)
        return dict(raw["templates"])

    def import_file(self, path: str) -> None:
        self.storage._require_lock()
        raw = VersionCatalogStore.read_file(self.paths.inside(path))
        self.storage.write("download-sources.json", raw, self.validate)
