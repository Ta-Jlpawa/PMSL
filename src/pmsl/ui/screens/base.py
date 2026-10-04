"""提供页面场景的准备、刷新、事件处理和绘制流程。"""

from typing import Any, Optional

from pmsl.domain.states import Page
from pmsl.ui.ports import SceneProvider
from pmsl.ui.widgets import Button, Scene


class SceneScreen:
    def __init__(self, page: Page, session: SceneProvider) -> None:
        self.page = page
        self.session = session
        self.scene = Scene((), ())
        self.hovered: Optional[Button] = None
        self.revision: Optional[int] = None

    def enter(self) -> None:
        try:
            if self.session.page is not self.page:
                self.session.select(self.page)
            self.scene = self.build_scene()
            self.revision = self.session.revision
            self.session.remember_view()
        except BaseException:
            self.session.restore_view()
            raise

    def build_scene(self) -> Scene:
        raise NotImplementedError("页面必须提供独立场景。")

    def leave(self) -> None:
        self.hovered = None

    def handle_event(self, event: Any) -> None:
        import pygame

        if event.type == pygame.MOUSEMOTION:
            self.hovered = next(
                (
                    button
                    for button in self.scene.buttons
                    if button.hover is not None and button.contains(tuple(event.pos), hover=True)
                ),
                None,
            )
        self.scene.handle_event(event)

    def update(self, seconds: float) -> None:
        revision = self.session.revision
        if revision != self.revision:
            try:
                self.scene = self.build_scene()
                self.revision = revision
                self.session.remember_view()
            except BaseException:
                self.session.restore_view()
                self.revision = self.session.revision
                raise
            self.hovered = None

    def render(self, surface: Any) -> None:
        self.scene.render(surface, self.hovered)
