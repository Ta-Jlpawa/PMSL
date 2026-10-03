"""关于作者页面保留原文案、链接与布局。"""

from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Scene


class AboutScreen(SceneScreen):
    def build_scene(self) -> Scene:
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        builder.image("about_authors", (0, 0))
        builder.button("home", "b_back", (20, 20), (150, 40), hover="b_back")
        builder.button("author-link", "none", (684, 168), (225, 52), hover="b_bg")
        builder.button("github-link", "none", (684, 358), (225, 52), hover="b_bg")
        return builder.build()
