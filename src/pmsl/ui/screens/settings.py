"""三个设置页共享生命周期，具名按钮对应现有设置行为。"""

from pmsl.domain.states import Page
from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Scene


class SettingsScreen(SceneScreen):
    def build_scene(self) -> Scene:
        view = self.session.settings_view()
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        number = {Page.PROGRAM_SETTINGS: 1, Page.DISPLAY_SETTINGS: 2, Page.OTHER_SETTINGS: 3}[
            self.page
        ]
        builder.image("pgm_setting_%s" % number, (0, 0))
        builder.button("home", "b_back_to_main", (32, 35), (178, 40), hover="b_title")
        previous = {
            Page.PROGRAM_SETTINGS: "previous-settings",
            Page.DISPLAY_SETTINGS: "program-settings",
            Page.OTHER_SETTINGS: "display-settings",
        }[self.page]
        following = {
            Page.PROGRAM_SETTINGS: "display-settings",
            Page.DISPLAY_SETTINGS: "other-settings",
            Page.OTHER_SETTINGS: "next-settings",
        }[self.page]
        builder.button(previous, "none", (300, 90), (35, 35), hover="b_bg")
        builder.button(following, "none", (665, 90), (35, 35), hover="b_bg")
        if self.page is Page.PROGRAM_SETTINGS:
            font = (
                view.console_font
                if len(view.console_font) <= 26
                else view.console_font[:23] + "..."
            )
            background = (
                view.console_background
                if len(view.console_background) <= 26
                else view.console_background[:23] + "..."
            )
            values = [
                ("test-java", (285, 176), (150, 30), "开始", 20),
                ("reset-java", (285, 218), (150, 30), "重置", 20),
                (
                    "java-path",
                    (285, 260),
                    (150, 30),
                    view.java if len(view.java) <= 16 else view.java[:13] + "...",
                    15,
                ),
                ("console-font", (285, 365), (300, 30), font, 20),
                ("console-background", (310, 418), (300, 30), background, 20),
                ("keywords", (285, 460), (150, 30), "默认", 20),
                ("colors", (665, 460), (150, 30), "默认", 20),
                ("save-log", (310, 500), (150, 30), str(view.save_server_log), 20),
                ("console-read-fix", (665, 500), (150, 30), "True", 20),
            ]
            for action, position, size, text, font_size in values:
                builder.button(
                    action, "b_bg_3", position, size, text, font_size=font_size, hover="b_bg_3"
                )
            png = "b_false" if view.external_console else "b_true"
            builder.button("external-console", png, (285, 311), (75, 35), hover="b_bg")
        elif self.page is Page.DISPLAY_SETTINGS:
            background = (
                view.background if len(view.background) <= 26 else view.background[:23] + "..."
            )
            builder.button(
                "fps", "b_bg_3", (285, 176), (150, 30), str(view.fps), font_size=25, hover="b_bg_3"
            )
            builder.button(
                "background",
                "b_bg_3",
                (285, 260),
                (300, 30),
                background,
                font_size=20,
                hover="b_bg_3",
            )
            builder.button(
                "interface-style",
                "b_bg_3",
                (285, 300),
                (150, 30),
                "默认",
                font_size=20,
                hover="b_bg_3",
            )
            builder.button(
                "dynamic-background",
                "b_true" if view.dynamic_background else "b_false",
                (285, 215),
                (75, 35),
                hover="b_bg",
            )
        return builder.build()
