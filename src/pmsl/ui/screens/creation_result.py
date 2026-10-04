"""绘制创建向导的下载进度、EULA 和完成页面。"""

from typing import Tuple

from pmsl.domain.states import CreationState, Page
from pmsl.ui.models import CreationView
from pmsl.ui.scene_builder import SceneBuilder
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.widgets import Image, Scene

PAGES = (Page.CREATE_DOWNLOAD, Page.CREATE_EULA, Page.CREATE_FINISH)


def download_status(view: CreationView) -> Tuple[str, tuple, int]:
    snapshot = view.snapshot
    if snapshot is None or snapshot.state is CreationState.EDITING:
        return "", (255, 255, 255), 0
    if snapshot.state is CreationState.DOWNLOADING:
        received = max(0, snapshot.received)
        if snapshot.total is None or snapshot.total <= 0:
            return "已接收 %d 字节" % received, (255, 255, 255), 0
        percent = min(100.0, round(100 * received / snapshot.total, 2))
        return " %" + str(percent), (255, 255, 255), min(770, int(770 * received / snapshot.total))
    if snapshot.state is CreationState.DOWNLOADED:
        text = "Fabric核心下载完成!" if view.input.selection.core == "Fabric" else "下载完成!"
        return text, (0, 255, 0), 0
    error = " ".join((snapshot.error or "PAUSE.").replace("\0", " ").split())
    return error[:160], (255, 0, 0), 0


class CreationResultScreen(SceneScreen):
    def _center(
        self,
        builder: SceneBuilder,
        text: str,
        position: tuple,
        area: tuple,
        color: tuple = (255, 255, 255),
        size: int = 20,
    ) -> None:
        rendered = self.session.visuals.text(text, size, color, False)
        point = (
            int(position[0] + (area[0] - rendered.get_width()) / 2),
            int(position[1] + (area[1] - rendered.get_height()) / 2),
        )
        builder.text(text, point, color, size)

    def build_scene(self) -> Scene:
        view = self.session.creation_view()
        builder = SceneBuilder(self.session.visuals, self.page.value, self.session.perform)
        if self.page is Page.CREATE_DOWNLOAD:
            builder.image("op_server_2", (0, 0))
            builder.button("back", "b_back", (20, 20), (150, 40), hover="b_back")
            builder.button("next", "b_next", (820, 538), (150, 40), hover="b_next")
            builder.button("download", "none", (301, 295), (150, 45), hover="b_title")
            builder.button("cancel", "none", (550, 295), (150, 45), hover="b_title")
            builder.button("tip", "none", (45, 370), (910, 130))
            for index, line in enumerate(view.tip_lines):
                builder.text(line, (60, 390 + index * 25), (255, 255, 255), 20)
            text, color, width = download_status(view)
            if width:
                image = view.progress_image or self.session.visuals.image("lg", (770, 20))
                builder.elements.append(Image(image, (114, 222), (0, 0, width, 20)))
            if text:
                self._center(builder, text, (111, 219), (776, 27), color, 15)
        elif self.page is Page.CREATE_EULA:
            builder.image("eula_1", (0, 0))
            ready = (
                view.eula_loaded
                and view.snapshot is not None
                and view.snapshot.state
                in {
                    CreationState.WAITING_FOR_EULA,
                    CreationState.COMMITTING,
                }
            )
            if ready:
                builder.button("refresh", "none", (291, 474), (200, 45), hover="b_bg_2")
                builder.button("accept", "none", (46, 474), (200, 45), hover="b_bg_2")
                builder.button("eula-link", "none", (537, 474), (200, 45), hover="b_bg_2")
                for index, line in enumerate(view.eula_lines):
                    builder.text(line, (63, 180 + index * 30), (255, 255, 255), 20)
            else:
                builder.button("refresh", "Loading", (0, 0), (1000, 600))
                if view.eula_error:
                    self._center(
                        builder, view.eula_error[:160], (63, 180), (874, 90), (255, 0, 0), 20
                    )
        else:
            builder.image("finish", (0, 0))
            current = view.input
            selection = current.selection
            kind = "插件服" if selection.core in {"Spigot", "Paper"} else "模组服"
            component = (
                str(selection.loader) + " " + str(selection.installer)
                if selection.core == "Fabric"
                else selection.build or "none"
            )
            values = (
                current.name,
                kind + " | " + selection.core,
                selection.minecraft_version + " | " + component,
                str(current.memory_gib) + " G",
            )
            for value, y in zip(values, (245, 307, 369, 430)):
                self._center(builder, value, (101, y), (800, 30))
            builder.button("finish", "none", (400, 490), (200, 42), hover="b_bg")
        return builder.build()
