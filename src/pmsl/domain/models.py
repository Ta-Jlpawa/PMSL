"""定义服务器资料、程序设置、启动参数和任务事件的数据模型。"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from pmsl.domain.states import CreationState

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CoreSelection:
    core: str
    minecraft_version: str
    build: Optional[str] = None
    loader: Optional[str] = None
    installer: Optional[str] = None


@dataclass(frozen=True)
class ServerProfile:
    id: str
    name: str
    selection: CoreSelection
    memory_gib: int
    directory: str
    icon: Optional[str] = None
    java: Optional[str] = None
    legacy_name: Optional[str] = None
    legacy_launch_script: Optional[str] = None
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class AppSettings:
    fps: int = 60
    dynamic_background: bool = True
    external_console: bool = True
    save_server_log: bool = False
    console_read_fix: bool = True
    java: Optional[str] = None
    console_font: Optional[str] = None
    console_background: Optional[str] = None
    background: Optional[str] = None
    loading_image: Optional[str] = None
    legacy_options: Dict[str, object] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class LaunchPlan:
    executable: str
    arguments: Tuple[str, ...]
    cwd: str
    environment: Dict[str, str] = field(default_factory=dict)
    encoding: str = "utf-8"
    external_console: bool = False


@dataclass
class CreationDraft:
    task_id: str
    name: str
    selection: CoreSelection
    memory_gib: int = 4
    eula_accepted: bool = False
    state: CreationState = CreationState.EDITING


@dataclass(frozen=True)
class TaskEvent:
    task_id: str
    kind: str
    payload: Dict[str, object] = field(default_factory=dict)
    server_id: Optional[str] = None
