"""加载、缩放并缓存图片和字体，按完整资源路径管理缓存。"""

from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from pmsl.domain.errors import PmslError
from pmsl.infrastructure.paths import AppPaths

Size = Tuple[int, int]
Color = Tuple[int, ...]


class Assets:
    def __init__(self, paths: AppPaths, text_limit: int = 512) -> None:
        self.paths = paths
        self.text_limit = text_limit
        self._images: Dict[Tuple[Path, Optional[Size], bool], Any] = {}
        self._fonts: Dict[Tuple[Path, int], Any] = {}
        self._texts: OrderedDict = OrderedDict()

    def _cached_path(self, path: Union[str, Path]) -> Path:
        import os

        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.paths.program_dir / candidate
        return Path(os.path.abspath(candidate))

    def load_image(
        self, path: Union[str, Path], size: Optional[Size] = None, alpha: bool = True
    ) -> Any:
        import pygame

        absolute = self.paths.inside(path)
        key = (absolute, size, alpha)
        if key not in self._images:
            if size is not None:
                source = self.load_image(absolute, alpha=alpha)
                image = pygame.transform.smoothscale(source, size)
            else:
                try:
                    source = pygame.image.load(str(absolute))
                except (OSError, pygame.error) as exc:
                    raise PmslError("无法读取图片：%s" % absolute) from exc
                image = source.convert_alpha() if alpha else source.convert()
            self._images[key] = image
        return self._images[key]

    def image(self, path: Union[str, Path], size: Optional[Size] = None, alpha: bool = True) -> Any:
        key = (self._cached_path(path), size, alpha)
        try:
            return self._images[key]
        except KeyError as exc:
            raise PmslError("图片未在页面进入前准备：%s" % path) from exc

    def load_font(self, path: Union[str, Path], size: int) -> Any:
        import pygame

        absolute = self.paths.inside(path)
        key = (absolute, size)
        if key not in self._fonts:
            try:
                self._fonts[key] = pygame.font.Font(str(absolute), size)
            except (OSError, pygame.error) as exc:
                raise PmslError("无法读取字体：%s" % absolute) from exc
        return self._fonts[key]

    def text(
        self,
        text: str,
        font_path: Union[str, Path],
        size: int,
        color: Color,
        global_alpha: bool = False,
    ) -> Any:
        absolute = self._cached_path(font_path)
        key = (absolute, size, text, color, global_alpha)
        if key not in self._texts:
            try:
                font = self._fonts[(absolute, size)]
            except KeyError as exc:
                raise PmslError("字体未在页面进入前准备：%s" % absolute) from exc
            self._texts[key] = font.render(text, True, color)
            if global_alpha and len(color) == 4:
                self._texts[key].set_alpha(color[3])
            if len(self._texts) > self.text_limit:
                self._texts.popitem(last=False)
        self._texts.move_to_end(key)
        return self._texts[key]

    def font(self, path: Union[str, Path], size: int) -> Any:
        try:
            return self._fonts[(self._cached_path(path), size)]
        except KeyError as exc:
            raise PmslError("字体未在页面进入前准备：%s" % path) from exc

    def invalidate_image(self, path: Union[str, Path]) -> None:
        absolute = self.paths.inside(path)
        for key in list(self._images):
            if key[0] == absolute:
                del self._images[key]

    def clear(self) -> None:
        self._texts.clear()
        self._fonts.clear()
        self._images.clear()
