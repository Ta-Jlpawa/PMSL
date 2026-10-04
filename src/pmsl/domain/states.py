"""定义界面页面、创建任务和服务器进程的状态枚举。"""

from enum import Enum


class Page(Enum):
    HOME = "home"
    WORLD_PROPERTIES = "world_properties"
    SERVER_PROPERTIES = "server_properties"
    PROGRAM_SETTINGS = "program_settings"
    DISPLAY_SETTINGS = "display_settings"
    OTHER_SETTINGS = "other_settings"
    ABOUT = "about"
    CREATE_TYPE = "create_type"
    CREATE_CORE = "create_core"
    CREATE_GAME_VERSION = "create_game_version"
    CREATE_CORE_VERSION = "create_core_version"
    CREATE_SETTINGS = "create_settings"
    CREATE_DOWNLOAD = "create_download"
    CREATE_EULA = "create_eula"
    CREATE_FINISH = "create_finish"
    CONSOLE = "console"


class CreationState(Enum):
    EDITING = "editing"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PREPARING = "preparing"
    WAITING_FOR_EULA = "waiting_for_eula"
    COMMITTING = "committing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
