"""创建前五步仅绘制输入快照和具名选择，保持原布局与文字居中。"""

from pmsl.domain.states import Page
from pmsl.ui.models import CreationView, VersionListView
from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Scene

PAGES = (
    Page.CREATE_TYPE,
    Page.CREATE_CORE,
    Page.CREATE_GAME_VERSION,
    Page.CREATE_CORE_VERSION,
    Page.CREATE_SETTINGS,
)


class CreationScreen(SceneScreen):
    def _header(self, builder: SceneBuilder, view: CreationView) -> None:
        selection = view.input.selection
        component = (
            ("L: " + str(selection.loader) + " I: " + str(selection.installer))
            if selection.core == "Fabric"
            else selection.build or "none"
        )
        values = [
            view.input.name + " | " + str(view.input.memory_gib) + " G",
            view.kind,
            selection.core,
            selection.minecraft_version,
            component,
            " | ",
        ]
        highlighted = PAGES.index(self.page)
        highlighted = (1, 2, 3, 4, 0)[highlighted]
        sizes = [25 if index == highlighted else 20 for index in range(6)]
        colors = [(239, 10, 106) if index == highlighted else (255, 255, 255) for index in range(6)]
        rendered = [
            self.session.visuals.text(text, size, color, True)
            for text, size, color in zip(values, sizes, colors)
        ]
        widths = [image.get_width() for image in rendered]
        # 原标题按分隔符宽度计算居中，沿用该计算保证像素一致。
        total = sum(width * 4 if width == widths[5] else width for width in widths)
        x = (1000 - total) // 2
        for index in range(5):
            builder.text(
                values[index],
                (x, 200 - rendered[index].get_height() // 2),
                colors[index],
                sizes[index],
            )
            x += widths[index]
            if index < 4:
                builder.text(" | ", (x, 200 - rendered[5].get_height() // 2), colors[5], sizes[5])
                x += widths[5]

    def _list(self, builder: SceneBuilder, view: VersionListView) -> None:
        y, flip_y, flip_height = (230, 520, 50)
        if view.component == "loader":
            flip_y, flip_height = 350, 30
        elif view.component == "installer":
            y, flip_height = 400, 30
        paging = {"game": "version", "build": "core"}.get(view.component, view.component)
        builder.button(
            "previous-" + paging + "-page",
            "b_bg_3",
            (350, flip_y),
            (100, flip_height),
            "上一页",
            font_size=20,
            hover="b_bg_3",
        )
        builder.button(
            "next-" + paging + "-page",
            "b_bg_3",
            (550, flip_y),
            (100, flip_height),
            "下一页",
            font_size=20,
            hover="b_bg_3",
        )
        for index, version in enumerate(view.values):
            builder.button(
                "select-" + view.component + ":" + version,
                "b_bg_3",
                (250, y + 40 * index),
                (500, 35),
                version,
                font_size=20,
                hover="b_bg_3",
            )

    def build_scene(self) -> Scene:
        view = self.session.creation_view()
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        number = PAGES.index(self.page) + 1
        builder.image("create_server_%s" % number, (0, 0))
        builder.button(
            "home" if self.page is Page.CREATE_TYPE else "back",
            "b_back",
            (20, 20),
            (150, 40),
            hover="b_back",
        )
        builder.button("next", "b_next", (820, 538), (150, 40), hover="b_next")
        if self.page in {Page.CREATE_TYPE, Page.CREATE_CORE}:
            if self.page is Page.CREATE_TYPE:
                choices, actions, logos = ("插件服", "模组服"), ("plugin", "mod"), ("plugin", "mod")
            elif view.kind == "插件服":
                choices, actions, logos = (
                    ("Spigot", "Paper"),
                    ("first-core", "second-core"),
                    ("spigot_logo", "papermc_logo"),
                )
            else:
                choices, actions, logos = (
                    ("Fabric", "Forge"),
                    ("first-core", "second-core"),
                    ("fabric_logo", "forge_logo"),
                )
            for index, (text, action) in enumerate(zip(choices, actions)):
                builder.button(
                    action, "b_bg_3", (250 + 300 * index, 250), (200, 200), hover="b_bg_3"
                )
                image = self.session.visuals.text(text, 30, (255, 255, 255), True)
                builder.text(
                    text,
                    (
                        250 + 300 * index + (200 - image.get_width()) // 2,
                        250 + (200 - image.get_height()) // 2 + 40,
                    ),
                    (255, 255, 255),
                    30,
                )
            for index, logo in enumerate(logos):
                forge = logo == "forge_logo"
                builder.image(
                    logo,
                    (310 + 300 * index - (20 if forge else 0), 280 - (20 if forge else 0)),
                    (120, 120) if forge else (80, 80),
                )
        elif self.page in {Page.CREATE_GAME_VERSION, Page.CREATE_CORE_VERSION}:
            if self.page is Page.CREATE_CORE_VERSION and view.input.selection.core == "Spigot":
                image = self.session.visuals.text(
                    "Spigot核心无需选择核心版本", 30, (255, 255, 255), False
                )
                builder.text(
                    "Spigot核心无需选择核心版本",
                    ((1000 - image.get_width()) // 2, (600 - image.get_height()) // 2),
                    (255, 255, 255),
                    30,
                )
            for listing in view.lists:
                self._list(builder, listing)
        else:
            for text, y in (
                ("在下方输入为服务器分配的运行内存(必须整数)", 245),
                ("*为创建的服务器命名", 370),
            ):
                image = self.session.visuals.text(text, 30, (255, 255, 255), False)
                builder.text(
                    text,
                    ((1000 - image.get_width()) // 2, int(y + (30 - image.get_height()) / 2)),
                    (255, 255, 255),
                    30,
                )
            memory = view.input.memory_gib
            color = next(
                (
                    rgb
                    for ceiling, rgb in (
                        (2, (232, 121, 46)),
                        (8, (116, 232, 46)),
                        (12, (46, 199, 232)),
                        (16, (232, 216, 46)),
                        (32, (46, 90, 232)),
                        (64, (232, 46, 46)),
                    )
                    if memory < ceiling
                ),
                (230, 46, 232),
            )
            builder.button(
                "memory",
                "b_bg_3",
                (350, 295),
                (300, 50),
                str(memory) + " GB",
                color=color,
                font_size=25,
                hover="b_bg_3",
            )
            builder.button(
                "name",
                "b_bg_3",
                (350, 420),
                (300, 50),
                view.input.name,
                font_size=25,
                hover="b_bg_3",
            )
        self._header(builder, view)
        return builder.build()
