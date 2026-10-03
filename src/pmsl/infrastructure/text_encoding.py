"""提示和 EULA 文本采用严格解码，保留 UTF-8 BOM 与中文 GBK。"""

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
