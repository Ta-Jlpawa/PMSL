"""严格解码 UTF-8、带 BOM 的 UTF-8 和 GBK 文本，返回文本及编码名称。"""

from typing import Tuple

from pmsl.domain.errors import StorageError


def decode_text(content: bytes) -> Tuple[str, str]:
    encodings = ("utf-8-sig",) if content.startswith(b"\xef\xbb\xbf") else ("utf-8", "gbk")
    for encoding in encodings:
        try:
            return content.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise StorageError("文本无法严格按 UTF-8 或 GBK 解码。")
