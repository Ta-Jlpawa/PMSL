"""管理页面创建、切换、更新和关闭。"""

from typing import Any, Callable, Dict, Optional, Protocol

from pmsl.domain.states import Page


class Screen(Protocol):
    def enter(self) -> None: ...
    def leave(self) -> None: ...
    def handle_event(self, event: Any) -> None: ...
    def update(self, seconds: float) -> None: ...
    def render(self, surface: Any) -> None: ...


class Navigation:
    def __init__(self, factories: Dict[Page, Callable[[], Screen]]) -> None:
        self.factories = factories
        self.page: Optional[Page] = None
        self.screen: Optional[Screen] = None

    def go(self, page: Page) -> None:
        candidate = self.factories[page]()
        # 先准备目标页面，成功后再替换当前页面。
        candidate.enter()
        if self.screen is not None:
            self.screen.leave()
        self.page = page
        self.screen = candidate

    def refresh(self) -> None:
        if self.page is not None:
            self.go(self.page)

    def close(self) -> None:
        if self.screen is not None:
            self.screen.leave()
        self.screen = None
        self.page = None
