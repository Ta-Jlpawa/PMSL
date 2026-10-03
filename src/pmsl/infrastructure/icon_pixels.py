"""固定图标尺寸的 RGBA 采样与遮罩；只使用标准库。"""

import math
import struct
from typing import List, Tuple

from pmsl.domain.errors import ValidationError

ICON_SIZE = (215, 397)


def _float32(value: float) -> float:
    return float(struct.unpack("<f", struct.pack("<f", value))[0])


def _axis(size: int, target: int, horizontal: bool) -> List[Tuple[int, int, int, int]]:
    samples = []
    for pixel in range(target):
        position = _float32((pixel + 0.5) / (target / size) - 0.5)
        first = math.floor(position)
        fraction = position - first
        if horizontal and (first < 0 or first >= size - 1):
            first, fraction = max(0, min(size - 1, first)), 0.0
        samples.append(
            (
                max(0, min(size - 1, first)),
                max(0, min(size - 1, first + 1)),
                round(_float32(1 - fraction) * 2048),
                round(fraction * 2048),
            )
        )
    return samples


def mask_span(row: int) -> Tuple[int, int]:
    # 原固定四边形的裁切边界：左边向下取整，右边沿裁切后的线段取最近像素。
    return 35 - (35 * row + 395) // 396, 214 - (34 * max(0, row - 11) + 192) // 385


def crop_rgba(source: bytes, size: Tuple[int, int]) -> bytes:
    width, height = size
    if width <= 0 or height <= 0 or len(source) != width * height * 4:
        raise ValidationError("图标 RGBA 数据尺寸不匹配。")
    target_width, target_height = ICON_SIZE
    result = bytearray(b"\xff\xff\xff\0" * target_width * target_height)
    if size == ICON_SIZE:
        result[:] = source
    else:
        columns = _axis(width, target_width, True)
        rows = _axis(height, target_height, False)
        for y, (top, bottom, upper, lower) in enumerate(rows):
            left_edge, right_edge = mask_span(y)
            for x in range(left_edge, right_edge + 1):
                left, right, a, b = columns[x]
                indices = (
                    (top * width + left) * 4,
                    (top * width + right) * 4,
                    (bottom * width + left) * 4,
                    (bottom * width + right) * 4,
                )
                destination = (y * target_width + x) * 4
                for channel in range(4):
                    first = source[indices[0] + channel] * a + source[indices[1] + channel] * b
                    second = source[indices[2] + channel] * a + source[indices[3] + channel] * b
                    # 保持原 8 位线性采样的系数精度及两阶段整数舍入。
                    top_value = (upper * (first >> 4)) >> 16
                    bottom_value = (lower * (second >> 4)) >> 16
                    result[destination + channel] = (top_value + bottom_value + 2) >> 2
    for y in range(target_height):
        left, right = mask_span(y)
        offset = y * target_width * 4
        result[offset : offset + left * 4] = b"\xff\xff\xff\0" * left
        result[offset + (right + 1) * 4 : offset + target_width * 4] = b"\xff\xff\xff\0" * (
            target_width - right - 1
        )
    return bytes(result)
