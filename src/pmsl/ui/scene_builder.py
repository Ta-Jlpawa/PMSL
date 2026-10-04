"""将图片、文字和按钮组合成页面场景。"""

from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pmsl.domain.errors import PmslError
from pmsl.ui.assets import Assets
from pmsl.ui.layouts import IMAGE_SCALES
from pmsl.ui.resources import FONT_FILE, FONT_SIZES, IMAGE_FILES
from pmsl.ui.widgets import Button, Image, Scene, Text


class Visuals:
    def __init__(self, assets: Assets) -> None:
        self.assets = assets
        self.font_path = assets.paths.resource(FONT_FILE)
        self._images: Dict[Tuple[str, Optional[Tuple[int, int]]], Any] = {}
        for name, relative in IMAGE_FILES.items():
            path = assets.paths.resource(relative)
            self._images[(name, None)] = assets.load_image(path)
            for size in IMAGE_SCALES.get(name, []):
                self._images[(name, size)] = assets.load_image(path, size)
        for font_size in FONT_SIZES:
            assets.load_font(self.font_path, font_size)

    def image(self, name: str, size: Optional[Tuple[int, int]] = None) -> Any:
        try:
            return self._images[(name, size)]
        except KeyError as exc:
            raise PmslError("页面图片或尺寸未准备：%s" % name) from exc

    def font(self, size: int) -> Any:
        return self.assets.font(self.font_path, size)

    def text(self, value: str, size: int, color: Tuple[int, ...], global_alpha: bool) -> Any:
        return self.assets.text(value, self.font_path, size, color, global_alpha=global_alpha)


class SceneBuilder:
    def __init__(self, visuals: Visuals, prefix: str, perform: Callable[[str], None]) -> None:
        self.visuals = visuals
        self.prefix = prefix
        self.perform = perform
        self.elements: List[Union[Image, Text]] = []
        self.buttons: List[Button] = []

    def image(
        self, name: str, position: Tuple[int, int], size: Optional[Tuple[int, int]] = None
    ) -> None:
        self.elements.append(Image(self.visuals.image(name, size), position))

    def text(
        self, value: str, position: Tuple[int, int], color: Tuple[int, ...], size: int
    ) -> None:
        self.elements.append(Text(self.visuals.text(value, size, color, True), position))

    def button(
        self,
        action: str,
        png: str,
        position: Tuple[int, int],
        size: Tuple[int, int],
        text: str = "",
        color: Tuple[int, ...] = (255, 255, 255),
        font_size: int = 15,
        hover: Optional[str] = None,
        sidebar: bool = False,
        inclusive_edges: bool = False,
    ) -> None:
        if png != "none":
            self.image(png, position, size)
        if text:
            rendered = self.visuals.text(text, font_size, color, False)
            width, height = rendered.get_size()
            point = (
                int(position[0] + (size[0] - width) / 2),
                int(position[1] + (size[1] - height) / 2),
            )
            self.elements.append(Text(rendered, point))
        key = self.prefix + "." + action
        self.buttons.append(
            Button(
                key,
                position,
                size,
                partial(self.perform, key),
                hover=self.visuals.image(hover, size) if hover else None,
                sidebar_hover=self.visuals.image("b_bg_title_main_2", (48, 48))
                if sidebar
                else None,
                inclusive_edges=inclusive_edges,
            )
        )

    def build(self) -> Scene:
        return Scene(tuple(self.elements), tuple(self.buttons))
