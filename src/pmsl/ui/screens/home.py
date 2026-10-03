"""首页场景，服务器业务通过兼容适配器调用。"""

from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Image, Scene


class HomeScreen(SceneScreen):
    def build_scene(self) -> Scene:
        view = self.session.home_view()
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        for image in ("title_winter", "serverlist", "button_text"):
            builder.image(image, (0, 0))
        for action, y in (
            ("create", 176),
            ("world-properties", 252),
            ("settings", 328),
            ("about", 404),
        ):
            builder.button(action, "none", (88, y), (229, 48), hover="b_bg_2", sidebar=True)
        builder.text(view.java_version, (630, 88), (255, 255, 255), 40)
        builder.text(str(view.server_count).zfill(2), (870, 98), (255, 255, 255), 35)
        selected = view.selected_index + 1 if view.server_count else 0
        builder.text(str(selected).zfill(2), (770, 68), (150, 249, 145), 55)
        if view.server_count == 0:
            builder.text("暂未创建服务器...", (500, 330), (255, 255, 255), 35)
        elif view.server_count > 99:
            builder.text("创建服务器过多...", (500, 330), (255, 255, 255), 35)
        else:
            builder.elements.append(Image(view.icon, (315, 158)))
            builder.image("server_name", (535, 170))
            builder.image("serverchange", (0, 0))
            builder.text(view.name or "", (540, 168), (255, 255, 255), 35)
            builder.text(view.summary or "", (540, 218), (255, 255, 255), 20)
            builder.text("服务器列表", (358, 165), (255, 255, 255, 100), 15)
            builder.button(
                "start", "b_title", (570, 500), (150, 40), "启动", font_size=25, hover="b_title"
            )
            builder.button(
                "delete", "b_title", (740, 500), (150, 40), "移除", (255, 0, 0), 25, "b_title"
            )
            builder.button(
                "previous-server",
                "none",
                (315, 531),
                (90, 24),
                "上一个",
                (0, 0, 0),
                hover="serverchange_bg",
            )
            builder.button(
                "next-server",
                "none",
                (405, 531),
                (90, 24),
                "下一个",
                (0, 0, 0),
                hover="serverchange_bg",
            )
            builder.button("rename", "b_re_name", (890, 170), (35, 32), hover="b_re_name")
            builder.button("icon", "b_re_icon", (886, 213), (35, 32), hover="b_re_icon")
            builder.button("console", "none", (0, 570), (1000, 30))
        return builder.build()
