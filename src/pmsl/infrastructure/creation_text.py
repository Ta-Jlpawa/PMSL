"""读取创建提示和 EULA，严格解码并限制 EULA 的显示长度。"""

from typing import List, Tuple

from pmsl.domain.errors import StorageError
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.text_encoding import decode_text

MAX_EULA_BYTES = 65536
MAX_EULA_LINES = 9


class CreationText:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def tips(self) -> Tuple[str, ...]:
        try:
            content, _ = decode_text(self.paths.resource("z_tip.txt").read_bytes())
        except (OSError, UnicodeError) as exc:
            raise StorageError("无法读取创建提示文本。") from exc
        return tuple(line for line in content.splitlines() if line.strip())

    def eula(self, directory: str) -> Tuple[str, ...]:
        path = self.paths.inside(self.paths.inside(directory) / "eula.txt")
        try:
            with path.open("rb") as handle:
                payload = handle.read(MAX_EULA_BYTES + 1)
            if len(payload) > MAX_EULA_BYTES:
                raise StorageError("EULA 文件过大，请检查创建目录。")
            content, _ = decode_text(payload)
        except (OSError, UnicodeError) as exc:
            raise StorageError("无法读取当前创建任务的 EULA 文件，请刷新或重新初始化。") from exc
        result: List[str] = []
        for line in content.splitlines():
            if "\0" in line:
                raise StorageError("EULA 文本包含无效控制字符。")
            result.extend(line[index : index + 75] for index in range(0, max(1, len(line)), 75))
            if len(result) > MAX_EULA_LINES:
                return tuple(result[: MAX_EULA_LINES - 1]) + ("...",)
        return tuple(result)
