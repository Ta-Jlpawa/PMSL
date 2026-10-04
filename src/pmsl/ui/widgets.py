"""定义图片、文字、按钮和场景，处理绘制与按钮命中检测。"""

from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Union

Point = Tuple[int, int]
Size = Tuple[int, int]
Color = Tuple[int, ...]


@dataclass(frozen=True)
class Image:
    surface: Any
    position: Point
    area: Optional[Tuple[int, ...]] = None

    def render(self, target: Any) -> None:
        target.blit(self.surface, self.position, self.area)


@dataclass(frozen=True)
class Text:
    surface: Any
    position: Point

    def render(self, target: Any) -> None:
        target.blit(self.surface, self.position)


@dataclass(frozen=True)
class Button:
    action: str
    position: Point
    size: Size
    callback: Callable[[], None]
    hover: Optional[Any] = None
    sidebar_hover: Optional[Any] = None
    inclusive_edges: bool = False

    def contains(self, point: Point, hover: bool = False) -> bool:
        x, y = point
        left, top = self.position
        width, height = self.size
        if self.inclusive_edges and not hover:
            return left <= x <= left + width and top <= y <= top + height
        return left <= x < left + width and top <= y < top + height

    def handle_event(self, event: Any) -> bool:
        import pygame

        if event.type == pygame.MOUSEBUTTONUP and self.contains(tuple(event.pos)):
            self.callback()
            return True
        return False

    def render_hover(self, target: Any) -> None:
        if self.hover is not None:
            target.blit(self.hover, self.position)
        if self.sidebar_hover is not None:
            target.blit(self.sidebar_hover, (self.position[0] - 57, self.position[1]))


@dataclass(frozen=True)
class Scene:
    elements: Tuple[Union[Image, Text], ...]
    buttons: Tuple[Button, ...]

    def render(self, target: Any, hovered: Optional[Button] = None) -> None:
        for element in self.elements:
            element.render(target)
        if hovered is not None:
            hovered.render_hover(target)

    def handle_event(self, event: Any) -> None:
        for button in self.buttons:
            if button.handle_event(event):
                break
