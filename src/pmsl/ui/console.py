"""控制台只负责输入和可见行绘制，不创建或判定进程。"""

from collections import OrderedDict
from typing import Any, Callable, List, Optional, Tuple

from pmsl.domain.runtime import LogSnapshot
from pmsl.infrastructure.process import MAX_LINE_LENGTH

HIGHLIGHTS = [
    ("error", (255, 0, 0)),
    ("decode error", (255, 0, 0)),
    ("[UTF-8]", (255, 0, 0)),
    ("info", (0, 255, 0)),
    ("warn", (255, 255, 0)),
    ("server thread", (0, 0, 255)),
    ("servermain", (0, 0, 255)),
    ("worker-main", (0, 0, 255)),
    ("starting server", (0, 255, 0)),
    ("done", (0, 255, 0)),
]
LINE_HIGHLIGHTS = [
    ("java", (255, 0, 255)),
    ("building", (198, 0, 225)),
    ("done", (0, 255, 105)),
    (">", (0, 230, 255)),
    ("stopping", (198, 0, 225)),
    ("saving", (198, 0, 225)),
    ("saved", (198, 0, 225)),
]


class ConsolePresenter:
    def __init__(
        self,
        font: Any,
        logs: Callable[[], LogSnapshot],
        send: Callable[[str], None],
        background: Optional[Any] = None,
    ) -> None:
        import pygame

        self.FONT = font
        self.LINE_HEIGHT = font.get_linesize()
        self.WIDTH, self.HEIGHT = 1000, 570
        self.INPUT_HEIGHT = self.LINE_HEIGHT + 10
        self.SCROLLBAR_WIDTH, self.PADDING = 12, 5
        self.screen = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.bg = background
        self.input_text, self.last_command = "", ""
        self.visible = False
        self.scroll_y = self.scroll_x = 0
        self.dragging_v = self.dragging_h = False
        self.drag_offset_y = self.drag_offset_x = 0
        self._logs, self._send = logs, send
        self._revision = -1
        self.output_lines: Tuple[str, ...] = ()
        self._surfaces: OrderedDict[str, Any] = OrderedDict()
        self._widths: OrderedDict[str, int] = OrderedDict()
        self.max_line_width = 0
        self.calculate_scroll()

    def _parts(self, text: str) -> List[Tuple[str, Tuple[int, int, int]]]:
        lowered = text.lower()
        base = next((color for word, color in LINE_HIGHLIGHTS if word in lowered), (255, 255, 255))
        parts = []
        index = 0
        while index < len(text):
            match = next(
                (
                    (word, color)
                    for word, color in HIGHLIGHTS
                    if lowered[index:].startswith(word.lower())
                ),
                None,
            )
            if match is not None:
                word, color = match
                parts.append((text[index : index + len(word)], color))
                index += len(word)
            else:
                parts.append((text[index], base))
                index += 1
        return parts

    def render_highlighted_line(self, text: str) -> Any:
        import pygame

        if text in self._surfaces:
            self._surfaces.move_to_end(text)
            return self._surfaces[text]
        surfaces = [self.FONT.render(part, True, color) for part, color in self._parts(text)]
        surface = pygame.Surface(
            (sum(s.get_width() for s in surfaces), self.LINE_HEIGHT), pygame.SRCALPHA
        )
        offset = 0
        for part in surfaces:
            surface.blit(part, (offset, 0))
            offset += part.get_width()
        self._surfaces[text] = surface
        if len(self._surfaces) > 128:
            self._surfaces.popitem(last=False)
        return surface

    def update_output(self) -> None:
        snapshot = self._logs()
        if self._revision == snapshot.revision:
            return
        old_count = len(self.output_lines)
        added = max(0, snapshot.revision - max(0, self._revision))
        self._revision = snapshot.revision
        self.output_lines = snapshot.lines
        if self.dragging_v:
            removed = max(0, old_count + added - len(self.output_lines))
            self.scroll_y = max(0, self.scroll_y - removed * self.LINE_HEIGHT)
        self._measure_widths()
        self.calculate_scroll()
        if not self.dragging_v:
            self.scroll_y = self.max_scroll_y

    def _measure_widths(self) -> None:
        widths = []
        for raw in self.output_lines:
            text = raw.rstrip()
            if text not in self._widths:
                self._widths[text] = sum(self.FONT.size(part)[0] for part, _ in self._parts(text))
            self._widths.move_to_end(text)
            widths.append(self._widths[text])
        while len(self._widths) > 5000:
            self._widths.popitem(last=False)
        self.max_line_width = max(widths, default=0)

    def calculate_scroll(self) -> None:
        self.visible_height = self.HEIGHT - self.INPUT_HEIGHT - self.SCROLLBAR_WIDTH - self.PADDING
        self.max_scroll_y = max(0, len(self.output_lines) * self.LINE_HEIGHT - self.visible_height)
        self.visible_width = self.WIDTH - self.SCROLLBAR_WIDTH - self.PADDING
        self.max_scroll_x = max(0, self.max_line_width - self.visible_width)
        self.scroll_y = min(self.scroll_y, self.max_scroll_y)
        self.scroll_x = min(self.scroll_x, self.max_scroll_x)
        self.scroll_bar_height = max(
            20, self.visible_height**2 // (self.LINE_HEIGHT * len(self.output_lines) + 1)
        )
        self.scroll_bar_y = int(
            self.scroll_y
            * (self.visible_height - self.scroll_bar_height)
            / max(1, self.max_scroll_y)
        )
        self.scroll_bar_width = max(20, self.visible_width**2 // (self.max_line_width + 1))
        self.scroll_bar_x = int(
            self.scroll_x * (self.visible_width - self.scroll_bar_width) / max(1, self.max_scroll_x)
        )

    def render(self) -> Any:
        import pygame

        if not self.visible:
            return self.screen
        self.calculate_scroll()
        self.screen.fill((0, 0, 0))
        if self.bg is not None:
            self.screen.blit(self.bg, (0, 0))
        start = self.scroll_y // self.LINE_HEIGHT
        for index in range(start, len(self.output_lines)):
            y = self.PADDING - self.scroll_y % self.LINE_HEIGHT + (index - start) * self.LINE_HEIGHT
            if y > self.visible_height + self.PADDING:
                break
            self.screen.blit(
                self.render_highlighted_line(self.output_lines[index].rstrip()),
                (self.PADDING - self.scroll_x, y),
            )
        pygame.draw.rect(
            self.screen,
            (30, 30, 30),
            (0, self.HEIGHT - self.INPUT_HEIGHT, self.WIDTH, self.INPUT_HEIGHT),
        )
        self.screen.blit(
            self.FONT.render(self.input_text, True, pygame.Color("green")),
            (self.PADDING, self.HEIGHT - self.INPUT_HEIGHT + 5),
        )
        pygame.draw.rect(
            self.screen,
            (80, 80, 80),
            (
                self.WIDTH - self.SCROLLBAR_WIDTH,
                self.PADDING + self.scroll_bar_y,
                self.SCROLLBAR_WIDTH,
                self.scroll_bar_height,
            ),
        )
        pygame.draw.rect(
            self.screen,
            (80, 80, 80),
            (
                self.PADDING + self.scroll_bar_x,
                self.HEIGHT - self.INPUT_HEIGHT - self.SCROLLBAR_WIDTH,
                self.scroll_bar_width,
                self.SCROLLBAR_WIDTH,
            ),
        )
        return self.screen

    def handle_event(self, event: Any) -> None:
        import pygame

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    self._send(self.input_text)
                    self.last_command, self.input_text = self.input_text, ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_UP:
                self.input_text = self.last_command
            elif event.key == pygame.K_DOWN:
                self.input_text = ""
            elif event.unicode and not any(c in event.unicode for c in "\r\n\x00"):
                self.input_text = (self.input_text + event.unicode)[:MAX_LINE_LENGTH]
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if (
                self.WIDTH - self.SCROLLBAR_WIDTH <= x <= self.WIDTH
                and self.PADDING + self.scroll_bar_y
                <= y
                <= self.PADDING + self.scroll_bar_y + self.scroll_bar_height
            ):
                self.dragging_v, self.drag_offset_y = True, y - self.scroll_bar_y
            if (
                self.HEIGHT - self.INPUT_HEIGHT - self.SCROLLBAR_WIDTH
                <= y
                <= self.HEIGHT - self.INPUT_HEIGHT
                and self.PADDING + self.scroll_bar_x
                <= x
                <= self.PADDING + self.scroll_bar_x + self.scroll_bar_width
            ):
                self.dragging_h, self.drag_offset_x = True, x - self.scroll_bar_x
            if event.button == 4:
                self.scroll_y = max(0, self.scroll_y - self.LINE_HEIGHT)
            elif event.button == 5:
                self.scroll_y = min(self.max_scroll_y, self.scroll_y + self.LINE_HEIGHT)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_v = self.dragging_h = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_v:
                bar = max(
                    0,
                    min(
                        self.visible_height - self.scroll_bar_height,
                        event.pos[1] - self.drag_offset_y,
                    ),
                )
                self.scroll_y = int(
                    bar * self.max_scroll_y / max(1, self.visible_height - self.scroll_bar_height)
                )
            if self.dragging_h:
                bar = max(
                    0,
                    min(
                        self.visible_width - self.scroll_bar_width,
                        event.pos[0] - self.drag_offset_x,
                    ),
                )
                self.scroll_x = int(
                    bar * self.max_scroll_x / max(1, self.visible_width - self.scroll_bar_width)
                )
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(
                0, min(self.max_scroll_y, self.scroll_y - event.y * self.LINE_HEIGHT)
            )

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def is_visible(self) -> bool:
        return self.visible
