"""注册页面并运行 Pygame 主循环，分发事件、更新状态和绘制界面。"""

from functools import partial
from typing import Any, Callable, Dict

from pmsl.domain.errors import PmslError
from pmsl.domain.states import Page
from pmsl.ui.navigation import Navigation, Screen
from pmsl.ui.ports import SceneProvider
from pmsl.ui.screens.about import AboutScreen
from pmsl.ui.screens.base import SceneScreen
from pmsl.ui.screens.console import ConsoleScreen
from pmsl.ui.screens.creation import PAGES as CREATION_PAGES
from pmsl.ui.screens.creation import CreationScreen
from pmsl.ui.screens.creation_result import PAGES as RESULT_PAGES
from pmsl.ui.screens.creation_result import CreationResultScreen
from pmsl.ui.screens.home import HomeScreen
from pmsl.ui.screens.properties import PropertiesScreen
from pmsl.ui.screens.settings import SettingsScreen


class App:
    def __init__(self, surface: Any, session: SceneProvider) -> None:
        self.surface = surface
        self.session = session
        factories: Dict[Page, Callable[[], Screen]] = {}
        for page in Page:
            screen_type = SceneScreen
            if page is Page.HOME:
                screen_type = HomeScreen
            elif page in {Page.WORLD_PROPERTIES, Page.SERVER_PROPERTIES}:
                screen_type = PropertiesScreen
            elif page in {Page.PROGRAM_SETTINGS, Page.DISPLAY_SETTINGS, Page.OTHER_SETTINGS}:
                screen_type = SettingsScreen
            elif page is Page.ABOUT:
                screen_type = AboutScreen
            elif page is Page.CONSOLE:
                screen_type = ConsoleScreen
            elif page in CREATION_PAGES:
                screen_type = CreationScreen
            elif page in RESULT_PAGES:
                screen_type = CreationResultScreen
            factories[page] = partial(screen_type, page, session)
        self.navigation = Navigation(factories)
        self.navigation.go(session.page)
        self.running = True

    def handle_event(self, event: Any) -> None:
        import pygame

        if event.type == pygame.QUIT:
            if self.session.request_exit():
                self.running = False
            return
        if self.navigation.screen is not None:
            self.navigation.screen.handle_event(event)
        self.session.handle_console_event(event)
        self._sync_page()

    def _sync_page(self) -> None:
        if self.navigation.page is not self.session.page:
            try:
                self.navigation.go(self.session.page)
            except BaseException:
                if isinstance(self.navigation.screen, SceneScreen):
                    self.navigation.screen.revision = self.session.revision
                raise

    def update(self, seconds: float) -> None:
        self.session.update()
        if self.session.should_exit:
            self.running = False
        self._sync_page()
        if self.navigation.screen is not None:
            self.navigation.screen.update(seconds)

    def render(self) -> None:
        self.session.draw_background(self.surface)
        if self.navigation.screen is not None:
            self.navigation.screen.render(self.surface)
        self.session.draw_overlays(self.surface)

    def run(self) -> int:
        import pygame

        while self.running:
            seconds = self.session.clock.tick(self.session.fps) / 1000
            for event in pygame.event.get():
                try:
                    self.handle_event(event)
                except (PmslError, OSError, ValueError) as exc:
                    self.session.confirm(text=str(exc), title="ERROR", buttons=["继续"])
            if not self.running:
                break
            try:
                self.update(seconds)
            except (PmslError, OSError, ValueError) as exc:
                self.session.confirm(text=str(exc), title="ERROR", buttons=["继续"])
            self.render()
            pygame.display.update()
        return 0

    def close(self) -> None:
        self.navigation.close()
