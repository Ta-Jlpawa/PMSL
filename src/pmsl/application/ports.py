"""定义应用服务读写服务器资料和程序设置所需的接口。"""

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
