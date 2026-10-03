"""页面只消费视图数据，不读取服务器文件。"""

from dataclasses import dataclass
from typing import Any, Optional

from pmsl.domain.creation import CreationSnapshot
from pmsl.domain.server_properties import PropertiesSnapshot
from pmsl.domain.versions import CreationInput


@dataclass(frozen=True)
class HomeView:
    server_count: int
    selected_index: int
    java_version: str
    name: Optional[str] = None
    summary: Optional[str] = None
    icon: Optional[Any] = None
    server_id: Optional[str] = None


@dataclass(frozen=True)
class SettingsView:
    fps: int
    external_console: bool
    dynamic_background: bool
    console_font: str
    console_background: str
    background: str
    java: str = "依据系统环境变量"
    save_server_log: bool = False


@dataclass(frozen=True)
class VersionListView:
    component: str
    values: tuple
    page: int
    page_count: int


@dataclass(frozen=True)
class CreationView:
    input: CreationInput
    kind: str
    lists: tuple = ()
    snapshot: Optional[CreationSnapshot] = None
    busy: bool = False
    eula_lines: tuple = ()
    tip_lines: tuple = ("Tip:  点击此处框框范围内,可以随机切换Tip语句哦!",)
    progress_image: Optional[Any] = None
    eula_loaded: bool = False
    eula_error: Optional[str] = None


@dataclass(frozen=True)
class PropertiesView:
    server_count: int
    selected_index: int
    snapshot: Optional[PropertiesSnapshot] = None
