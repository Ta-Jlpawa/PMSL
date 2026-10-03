"""属性编辑的只读快照，键名与显示名称分离。"""

from dataclasses import dataclass
from typing import Optional, Tuple

EDITABLE_KEYS = (
    "level-seed",
    "level-name",
    "gamemode",
    "difficulty",
    "force-gamemode",
    "allow-nether",
    "enable-command-block",
    "pvp",
    "spawn-npcs",
    "spawn-animals",
    "spawn-monsters",
    "generate-structures",
    "motd",
    "server-port",
    "max-players",
    "simulation-distance",
    "player-idle-timeout",
    "online-mode",
    "white-list",
    "prevent-proxy-connections",
    "allow-flight",
)


@dataclass(frozen=True)
class PropertiesSnapshot:
    server_id: str
    name: str
    values: Tuple[Tuple[str, Optional[str]], ...]
    available: bool = True

    def get(self, key: str) -> Optional[str]:
        return next((value for field, value in self.values if field == key), None)
