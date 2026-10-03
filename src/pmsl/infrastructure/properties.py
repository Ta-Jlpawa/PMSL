"""保留未修改字节的 Java properties 编辑器。"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from pmsl.domain.errors import ValidationError
from pmsl.domain.validation import validate_legacy_name
from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.paths import AppPaths, PathValue


def _unescape(value: str) -> str:
    result: List[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        index += 1
        if character != "\\" or index == len(value):
            result.append(character)
            continue
        character = value[index]
        index += 1
        if character == "u":
            digits = value[index : index + 4]
            if len(digits) != 4 or re.fullmatch(r"[0-9a-fA-F]{4}", digits) is None:
                raise ValidationError("属性文件包含无效的 Unicode 转义。")
            result.append(chr(int(digits, 16)))
            index += 4
        else:
            result.append({"t": "\t", "r": "\r", "n": "\n", "f": "\f"}.get(character, character))
    # Java 的两个 UTF-16 转义可组成一个非 BMP 字符。
    return "".join(result).encode("utf-16-le", "surrogatepass").decode("utf-16-le", "surrogatepass")


def _escape(value: str) -> str:
    result = []
    for index, character in enumerate(value):
        escaped = {"\\": "\\\\", "\t": r"\t", "\r": r"\r", "\n": r"\n", "\f": r"\f"}
        if character in escaped:
            result.append(escaped[character])
        elif character == " " and index == 0:
            result.append(r"\ ")
        elif ord(character) < 32 or ord(character) > 126:
            encoded = character.encode("utf-16-be", "surrogatepass")
            result.extend(
                "\\u%04x" % int.from_bytes(encoded[i : i + 2], "big")
                for i in range(0, len(encoded), 2)
            )
        else:
            result.append(character)
    return "".join(result)


@dataclass
class _Entry:
    raw: str
    key: Optional[str] = None
    value: str = ""
    prefix: str = ""
    ending: str = ""


class PropertiesDocument:
    def __init__(self, content: str, encoding: str = "utf-8") -> None:
        self.encoding = encoding
        self.entries: List[_Entry] = []
        lines = re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$", content)
        index = 0
        while index < len(lines):
            raw = lines[index]
            logical = raw.rstrip("\r\n")
            index += 1
            comment = logical.lstrip(" \t\f").startswith(("#", "!"))
            while not comment and (len(logical) - len(logical.rstrip("\\"))) % 2:
                logical = logical[:-1]
                if index == len(lines):
                    break
                raw += lines[index]
                logical += lines[index].rstrip("\r\n").lstrip(" \t\f")
                index += 1
            ending = re.search(r"(\r\n|\r|\n)$", raw)
            entry = _Entry(raw, ending=ending.group() if ending else "")
            start = len(logical) - len(logical.lstrip(" \t\f"))
            if not comment and start < len(logical):
                stop = start
                escaped = False
                while stop < len(logical):
                    character = logical[stop]
                    if not escaped and character in "=: \t\f":
                        break
                    escaped = character == "\\" and not escaped
                    stop += 1
                value_start = stop
                while value_start < len(logical) and logical[value_start] in " \t\f":
                    value_start += 1
                if value_start < len(logical) and logical[value_start] in "=:":
                    value_start += 1
                while value_start < len(logical) and logical[value_start] in " \t\f":
                    value_start += 1
                entry.key = _unescape(logical[start:stop])
                entry.value = _unescape(logical[value_start:])
                entry.prefix = logical[:value_start]
                if value_start == stop == len(logical):
                    entry.prefix += "="
            self.entries.append(entry)

    @classmethod
    def read(
        cls, paths: AppPaths, path: PathValue, encoding: Optional[str] = None
    ) -> "PropertiesDocument":
        payload = paths.inside(path).read_bytes()
        if encoding is not None:
            return cls(payload.decode(encoding), encoding)
        encodings = (
            ("utf-8-sig",)
            if payload.startswith(b"\xef\xbb\xbf")
            else ("utf-8", "gbk", "iso-8859-1")
        )
        for candidate in encodings:
            try:
                return cls(payload.decode(candidate), candidate)
            except UnicodeDecodeError:
                continue
        raise ValidationError("属性文件编码无法识别。")

    def get(self, key: str) -> Optional[str]:
        return next((entry.value for entry in reversed(self.entries) if entry.key == key), None)

    def values(self) -> Dict[str, str]:
        return {entry.key: entry.value for entry in self.entries if entry.key is not None}

    def set(self, key: str, value: str) -> None:
        entry = next((entry for entry in reversed(self.entries) if entry.key == key), None)
        if entry is None:
            raise ValidationError("当前服务器配置不存在属性：%s" % key)
        if entry.value == value:
            return
        entry.raw = entry.prefix + _escape(value) + entry.ending
        entry.value = value

    def to_bytes(self) -> bytes:
        return "".join(entry.raw for entry in self.entries).encode(self.encoding)

    def save(self, paths: AppPaths, path: PathValue) -> None:
        atomic_write(paths, path, self.to_bytes())


BOOLEAN_KEYS = {
    "allow-flight",
    "allow-nether",
    "enable-command-block",
    "force-gamemode",
    "generate-structures",
    "hardcore",
    "pvp",
    "spawn-animals",
    "spawn-monsters",
    "spawn-npcs",
    "white-list",
    "online-mode",
    "prevent-proxy-connections",
    "enable-status",
    "hide-online-players",
}


def validate_property(key: str, value: str) -> None:
    if key in BOOLEAN_KEYS and value not in {"true", "false"}:
        raise ValidationError("布尔属性只能填写 true 或 false。")
    enums = {
        "gamemode": {"survival", "creative", "adventure", "spectator"},
        "difficulty": {"peaceful", "easy", "normal", "hard"},
    }
    if key in enums and value not in enums[key]:
        raise ValidationError("%s 的可选值为：%s" % (key, ", ".join(sorted(enums[key]))))
    ranges = {
        "server-port": (1, 65535),
        "max-players": (1, 2147483647),
        "simulation-distance": (3, 32),
        "player-idle-timeout": (0, 2147483647),
    }
    if key in ranges:
        low, high = ranges[key]
        if re.fullmatch(r"[0-9]+", value) is None or not low <= int(value) <= high:
            raise ValidationError("%s 必须为 %d—%d 之间的整数。" % (key, low, high))
    if key == "level-name":
        validate_legacy_name(value)
