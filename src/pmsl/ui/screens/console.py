"""控制台仅准备原底部返回按钮；日志由独立控制台组件绘制。"""

from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Scene


class ConsoleScreen(SceneScreen):
    def build_scene(self) -> Scene:
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        builder.button("hide-console", "none", (0, 570), (1000, 30))
        return builder.build()
