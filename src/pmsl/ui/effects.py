"""只操作已准备 Surface 的背景跟随与提示动画。"""

import math
import time
from typing import Any, Callable, Optional, Tuple

from pmsl.domain.errors import ValidationError
from pmsl.ui.widgets import Point, Size


class BackgroundFollower:
    def __init__(
        self, image: Any, window_size: Size, ease: float = 0.1, enabled: bool = True
    ) -> None:
        self.image, self.window_size = image, window_size
        self.ease, self.enabled = ease, enabled
        width, height = image.get_size()
        self.max_offset_x = width - window_size[0]
        self.max_offset_y = height - window_size[1]
        self.offset_x: float = self.max_offset_x // 2
        self.offset_y: float = self.max_offset_y // 2

    def update(self, mouse: Point) -> None:
        if not self.enabled:
            return
        width, height = self.window_size
        dx = (mouse[0] - width / 2) / (width / 2)
        dy = (mouse[1] - height / 2) / (height / 2)
        target_x = self.max_offset_x * dx / 2 + self.max_offset_x / 2
        target_y = self.max_offset_y * dy / 2 + self.max_offset_y / 2
        self.offset_x += (target_x - self.offset_x) * self.ease
        self.offset_y += (target_y - self.offset_y) * self.ease
        self.offset_x = max(0, min(self.offset_x, self.max_offset_x))
        self.offset_y = max(0, min(self.offset_y, self.max_offset_y))

    def render(self, target: Any) -> None:
        target.blit(self.image, (-self.offset_x, -self.offset_y))


class ImageAnimation:
    def __init__(
        self,
        image: Any,
        start_pos: Point,
        end_pos: Point,
        duration: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not math.isfinite(duration) or duration <= 0:
            raise ValidationError("动画时长必须为有限正数。")
        self.image, self.rect = image, image.get_rect()
        self.start_pos, self.end_pos = start_pos, end_pos
        self.duration, self.clock = duration, clock
        self.started_at: Optional[float] = None

    def start(self) -> None:
        self.started_at = self.clock()

    def stop(self) -> None:
        self.started_at = None

    def position(self, elapsed: float) -> Tuple[float, float]:
        progress = min(1.0, max(0.0, elapsed / self.duration))
        eased = 3 * progress**2 - 2 * progress**3
        return (
            self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * eased,
            self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * eased,
        )

    def render(self, target: Any) -> None:
        if self.started_at is None:
            return
        self.rect.center = self.position(self.clock() - self.started_at)
        target.blit(self.image, self.rect)
