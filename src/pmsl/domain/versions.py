"""定义核心版本目录和创建输入，校验游戏与核心组件的版本组合。"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from pmsl.domain.errors import ValidationError
from pmsl.domain.models import CoreSelection

SUPPORTED_CORES = ("Spigot", "Paper", "Fabric", "Forge")


def validate_version(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-zA-Z][0-9a-zA-Z._+\-]*", value) is None:
        raise ValidationError("版本标识无效：%s" % value)
    return value


@dataclass(frozen=True)
class CoreBuild:
    version: str
    paper_code: Optional[str] = None


@dataclass(frozen=True)
class GameRelease:
    core: str
    version: str
    builds: Tuple[CoreBuild, ...] = ()


@dataclass(frozen=True)
class VersionCatalog:
    games: Tuple[GameRelease, ...]
    fabric_loaders: Tuple[str, ...]
    fabric_installers: Tuple[str, ...]

    def versions(self, core: str) -> Tuple[str, ...]:
        return tuple(game.version for game in self.games if game.core == core)

    def release(self, core: str, version: str) -> GameRelease:
        for game in self.games:
            if game.core == core and game.version == version:
                return game
        raise ValidationError("离线目录中没有 %s / %s。" % (core, version))

    def select(self, core: str, version: Optional[str] = None) -> CoreSelection:
        versions = self.versions(core)
        if not versions:
            raise ValidationError("离线目录中没有该核心。")
        selected = version if version in versions else versions[0]
        game = self.release(core, selected)
        return CoreSelection(
            core,
            selected,
            game.builds[0].version if game.builds else None,
            self.fabric_loaders[0] if core == "Fabric" else None,
            self.fabric_installers[0] if core == "Fabric" else None,
        )

    def validate_selection(self, selection: CoreSelection) -> None:
        game = self.release(selection.core, selection.minecraft_version)
        if selection.core in {"Paper", "Forge"}:
            if (
                selection.build not in {item.version for item in game.builds}
                or selection.loader is not None
                or selection.installer is not None
            ):
                raise ValidationError("构建号与所选游戏版本不匹配。")
        elif selection.core == "Fabric":
            if (
                selection.build is not None
                or selection.loader not in self.fabric_loaders
                or selection.installer not in self.fabric_installers
            ):
                raise ValidationError("Fabric 必须选择有效的 Loader 和 Installer。")
        elif (
            selection.build is not None
            or selection.loader is not None
            or selection.installer is not None
        ):
            raise ValidationError("Spigot 不需要单独选择核心构建。")


@dataclass(frozen=True)
class CreationInput:
    name: str
    selection: CoreSelection
    memory_gib: int = 4
