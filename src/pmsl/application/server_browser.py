"""管理服务器列表与当前选择，按服务器 ID 保留选择并生成概要。"""

from dataclasses import dataclass, replace
from typing import Optional, Tuple

from pmsl.domain.errors import ValidationError
from pmsl.domain.models import ServerProfile


@dataclass(frozen=True)
class BrowserSnapshot:
    profiles: Tuple[ServerProfile, ...] = ()
    selected_id: Optional[str] = None

    @property
    def index(self) -> int:
        return next(
            (i for i, profile in enumerate(self.profiles) if profile.id == self.selected_id), 0
        )

    @property
    def selected(self) -> Optional[ServerProfile]:
        return self.profiles[self.index] if self.profiles else None


class ServerBrowser:
    def __init__(self) -> None:
        self.current = BrowserSnapshot()

    def refresh(
        self, profiles: Tuple[ServerProfile, ...], preferred_id: Optional[str] = None
    ) -> None:
        ids = {profile.id for profile in profiles}
        names = {profile.name.casefold() for profile in profiles}
        if len(ids) != len(profiles) or len(names) != len(profiles):
            raise ValidationError("目录包含重复 ID 或显示名称，不能继续管理。")
        selected = preferred_id or self.current.selected_id
        if selected not in ids:
            selected = profiles[min(self.current.index, len(profiles) - 1)].id if profiles else None
        self.current = BrowserSnapshot(profiles, selected)

    def move(self, offset: int) -> None:
        if self.current.profiles:
            index = (self.current.index + offset) % len(self.current.profiles)
            self.current = replace(self.current, selected_id=self.current.profiles[index].id)


def server_summary(profile: ServerProfile) -> str:
    selection = profile.selection
    version = selection.loader if selection.core == "Fabric" else selection.build or "none"
    return "%s / %s / %s (%sG)" % (
        selection.core,
        selection.minecraft_version,
        version,
        profile.memory_gib,
    )
