"""应用层所需的存储能力由组装处提供。"""

from typing import List, Protocol

from pmsl.domain.models import AppSettings, ServerProfile


class ServerStore(Protocol):
    def list(self) -> List[ServerProfile]: ...

    def get(self, server_id: str) -> ServerProfile: ...

    def save(self, profile: ServerProfile) -> None: ...

    def remove(self, server_id: str) -> None: ...


class SettingsStore(Protocol):
    def load(self) -> AppSettings: ...

    def save(self, settings: AppSettings) -> None: ...
