"""将图标编码为 PNG，并按服务器 ID 保存到对应服务器目录。"""

import io
import struct
from pathlib import Path

from pmsl.domain.errors import StorageError, ValidationError
from pmsl.infrastructure.catalog import JsonServerStore
from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.icon_pixels import ICON_SIZE, crop_rgba
from pmsl.infrastructure.server_layout import ServerLayout
from pmsl.infrastructure.storage import JsonStorage

MAX_BYTES = 16 * 1024 * 1024
MAX_PIXELS = 16 * 1024 * 1024


def encode_icon(source: Path) -> bytes:
    import pygame

    if source.suffix.lower() != ".png":
        raise ValidationError("服务器标识图必须为 PNG 文件。")
    try:
        with source.open("rb") as handle:
            payload = handle.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValidationError("服务器标识图超过 16 MiB。")
        if len(payload) < 33 or payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
            raise ValidationError("无法读取选择的 PNG 标识图。")
        width, height, depth = struct.unpack(">IIB", payload[16:25])
        if depth > 8 or width == 0 or height == 0:
            raise ValidationError("请使用位深不超过 8 位的 PNG。")
        if width * height > MAX_PIXELS:
            raise ValidationError("服务器标识图像素数量过大。")
        image = pygame.image.load(io.BytesIO(payload), "icon.png")
        if image.get_size() != (width, height):
            raise ValidationError("PNG 解码尺寸与文件头不一致。")
        pixels = crop_rgba(pygame.image.tostring(image, "RGBA"), (width, height))
        prepared = pygame.image.frombuffer(pixels, ICON_SIZE, "RGBA")
        output = io.BytesIO()
        pygame.image.save(prepared, output, "icon.png")
        return output.getvalue()
    except (OSError, pygame.error, ValueError) as exc:
        raise StorageError("无法处理选择的服务器标识图。") from exc


class ServerIcons:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage, self.paths = storage, storage.paths
        self.store = JsonServerStore(storage)
        self.layout = ServerLayout(self.paths)

    def save(self, server_id: str, payload: bytes) -> Path:
        self.storage._require_lock()
        profile = self.store.get(server_id)
        target = self.layout.file(profile, "icon.png")
        atomic_write(self.paths, target, payload)
        return target
