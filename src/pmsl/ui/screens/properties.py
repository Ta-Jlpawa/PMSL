"""两页属性仅消费快照，保持原点击区域、数值与布尔按钮布局。"""

from pmsl.domain.states import Page
from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Scene

WORLD_TEXT = (
    ("seed", "level-seed", 495, 153, 462, 515),
    ("world-name", "level-name", 495, 208, 457, 515),
    ("gamemode", "gamemode", 495, 263, 452, 515),
    ("difficulty", "difficulty", 495, 318, 447, 515),
)
SERVER_TEXT = (
    ("motd", "motd", 529, 153, 428, 515),
    ("port", "server-port", 529, 208, 422, 515),
    ("max-players", "max-players", 529, 263, 417, 515),
    ("simulation-distance", "simulation-distance", 495, 318, 447, 515),
    ("idle-timeout", "player-idle-timeout", 664, 373, 273, 655),
)
WORLD_BOOL = (
    ("force-gamemode", 575, 390),
    ("allow-nether", 575, 435),
    ("enable-command-block", 575, 480),
    ("pvp", 575, 525),
    ("spawn-npcs", 845, 390),
    ("spawn-animals", 845, 435),
    ("spawn-monsters", 845, 480),
    ("generate-structures", 845, 525),
)
SERVER_BOOL = (
    ("online-mode", 536, 435),
    ("white-list", 536, 480),
    ("prevent-proxy-connections", 656, 525),
    ("allow-flight", 846, 435),
)


class PropertiesScreen(SceneScreen):
    def build_scene(self) -> Scene:
        view = self.session.properties_view()
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        world = self.page is Page.WORLD_PROPERTIES
        builder.image("set_world" if world else "set_server", (0, 0))
        builder.button("home", "none", (58, 46), (200, 44), hover="b_title")
        builder.button(
            "server-properties" if world else "world-properties",
            "b_title_next" if world else "b_title_back",
            (615, 53),
            (32, 32),
            hover="b_bg",
        )
        builder.button("switch-server", "none", (58, 113), (200, 44), hover="b_title")
        fields = WORLD_TEXT if world else SERVER_TEXT
        for action, _, x, y, width, _ in fields:
            builder.button(action, "none", (x, y), (width, 38))
        snapshot = view.snapshot
        if snapshot is None:
            builder.text("暂未创建服务器...", (460, 102), (249, 238, 145), 20)
        else:
            builder.text(snapshot.name, (460, 102), (150, 249, 145), 20)
            for _, key, _, y, _, x in fields:
                value = snapshot.get(key)
                if value is not None:
                    text = value.replace("\n", r"\n").replace("\r", r"\r").replace("\0", "")
                    builder.text(
                        text[:32] + "..." if len(text) >= 32 else text,
                        (x, y + 8),
                        (255, 255, 255),
                        20,
                    )
            for key, x, y in WORLD_BOOL if world else SERVER_BOOL:
                value = snapshot.get(key)
                if value in {"true", "false"}:
                    builder.button(
                        "toggle-" + key,
                        "b_" + value,
                        (x, y),
                        (75, 35),
                        hover="b_bg",
                        inclusive_edges=True,
                    )
            builder.text(str(view.server_count).zfill(2), (170, 523), (255, 255, 255), 35)
            builder.text(str(view.selected_index + 1).zfill(2), (100, 513), (150, 249, 145), 35)
        return builder.build()
