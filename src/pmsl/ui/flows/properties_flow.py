"""属性页具名动作与稳定 ID 选择；弹窗在主线程执行。"""

from typing import TYPE_CHECKING, Optional, Tuple

from pmsl.application.property_editor import PropertyEditor
from pmsl.domain.errors import PmslError
from pmsl.domain.server_properties import PropertiesSnapshot
from pmsl.domain.states import Page
from pmsl.infrastructure.server_properties import ServerPropertyStore
from pmsl.ui.models import PropertiesView

if TYPE_CHECKING:
    from pmsl.ui.session import UiSession

FIELDS = {
    "world_properties.seed": (
        "level-seed",
        "请输入世界种子\n请注意,更换种子后须重创建世界才能生效",
    ),
    "world_properties.world-name": ("level-name", "请输入世界名称\n将作为世界名称及其文件夹名"),
    "world_properties.gamemode": (
        "gamemode",
        "请输入默认游戏模式\n可输入\n[survival-生存,creative-创造,adventure-冒险,spectator-旁观]",
    ),
    "world_properties.difficulty": (
        "difficulty",
        "请输入目标难度\n可输入\n[peaceful-和平,easy-简单,normal-普通,hard-困难]",
    ),
    "server_properties.motd": (
        "motd",
        "请输入要展示的服务器信息(为Unicode码)\n可输入的字符数 [0-59]",
    ),
    "server_properties.port": ("server-port", "请输入服务器(监听的)端口号\n可输入的范围 [1-65534]"),
    "server_properties.max-players": ("max-players", "请输入服务器支持的最大玩家数量"),
    "server_properties.simulation-distance": (
        "simulation-distance",
        "请输入玩家各个方向上可视的区块数量(以玩家为中心的半径)\n可输入的范围 [3-32]",
    ),
    "server_properties.idle-timeout": (
        "player-idle-timeout",
        "请输入玩家被允许的最长挂机时间(单位:分钟)\n设置为0表示关闭此功能",
    ),
}
BOOLEANS = {
    Page.WORLD_PROPERTIES: (
        "force-gamemode",
        "allow-nether",
        "enable-command-block",
        "pvp",
        "spawn-npcs",
        "spawn-animals",
        "spawn-monsters",
        "generate-structures",
    ),
    Page.SERVER_PROPERTIES: (
        "online-mode",
        "white-list",
        "prevent-proxy-connections",
        "allow-flight",
    ),
}


class PropertiesFlow:
    def __init__(self, session: "UiSession") -> None:
        self.session = session
        self.editor = PropertyEditor(ServerPropertyStore(session.storage))
        self.selected_id: Optional[str] = None
        self.ids: Tuple[str, ...] = ()
        self._prepared: Optional[
            Tuple[Tuple[str, ...], Optional[str], Optional[PropertiesSnapshot]]
        ] = None

    def remember_view(self) -> None:
        self._prepared = self.ids, self.selected_id, self.editor.current

    def restore_view(self) -> None:
        if self._prepared is not None:
            self.ids, self.selected_id, self.editor.current = self._prepared

    def on_enter(self) -> None:
        session = self.session
        profiles = session.server_profiles()
        ids = tuple(profile.id for profile in profiles)
        if not ids:
            self.ids = ()
            self.selected_id, self.editor.current = None, None
            return
        selected = self.selected_id if self.selected_id in ids else ids[0]
        assert selected is not None
        self.editor.store = ServerPropertyStore(session.storage)
        snapshot = self.editor.store.load(selected)
        self.ids, self.selected_id, self.editor.current = ids, selected, snapshot
        if not snapshot.available:
            session.confirm(
                text="[ERROR] : 读取错误. \n读取server_properties文件时未找到文件",
                title="ERROR",
                buttons=["继续"],
            )

    def view(self) -> PropertiesView:
        index = self.ids.index(self.selected_id) if self.selected_id in self.ids else 0
        return PropertiesView(len(self.ids), index, self.editor.current)

    def handle(self, action: str) -> bool:
        session = self.session
        if session.page is Page.HOME and action == "home.world-properties":
            previous = self.selected_id
            profile = session.home.browser.current.selected
            if profile is not None:
                self.selected_id = profile.id
            try:
                session.select(Page.WORLD_PROPERTIES)
            except BaseException:
                self.selected_id = previous
                raise
            return True
        if session.page not in {Page.WORLD_PROPERTIES, Page.SERVER_PROPERTIES}:
            return False
        if not action.startswith(session.page.value + "."):
            raise PmslError("属性动作不属于当前页面。")
        suffix = action.split(".", 1)[1]
        if suffix == "home":
            session.select(Page.HOME)
            return True
        if suffix in {"server-properties", "world-properties"}:
            session.select(
                Page.SERVER_PROPERTIES if suffix == "server-properties" else Page.WORLD_PROPERTIES
            )
            return True
        if suffix == "switch-server":
            if self.ids:
                index = self.ids.index(self.selected_id) if self.selected_id in self.ids else -1
                previous = self.selected_id
                self.selected_id = self.ids[(index + 1) % len(self.ids)]
                try:
                    session.select(session.page)
                except BaseException:
                    self.selected_id = previous
                    raise
            return True
        snapshot = self.editor.current
        if snapshot is None:
            return True
        self.editor.store = ServerPropertyStore(session.storage)
        if action in FIELDS:
            key, text = FIELDS[action]
            current = snapshot.get(key)
            if current is None:
                raise PmslError("当前服务器未提供此属性，未写入。")
            value = session.prompt(text=text, title=session.title, default=current)
            if value is None:
                session.confirm(
                    text="你关闭了界面,此次输入将不做保存.", title=session.title, buttons=["继续"]
                )
                return True
        elif suffix.startswith("toggle-"):
            key = suffix[7:]
            current = snapshot.get(key)
            if key not in BOOLEANS[session.page] or current not in {"true", "false"}:
                raise PmslError("该布尔属性缺失或值无效，未修改。")
            value = "false" if current == "true" else "true"
        else:
            raise PmslError("未知属性动作。")
        self.editor.change(key, value)
        return True
