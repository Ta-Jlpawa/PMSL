"""构建控制台页面的返回按钮场景。"""

from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Scene


class ConsoleScreen(SceneScreen):
    def build_scene(self) -> Scene:
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        builder.button("hide-console", "none", (0, 570), (1000, 30))
        return builder.build()
