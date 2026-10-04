"""校验服务器名称、Windows 目录名和正整数参数。"""

import re

from pmsl.domain.errors import ValidationError


def validate_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("服务器名称不能为空。")
    if any(ord(character) < 32 or ord(character) == 127 for character in name):
        raise ValidationError("服务器名称不能包含控制字符。")
    return name


def validate_legacy_name(name: str) -> str:
    validate_name(name)
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update("COM%d" % n for n in range(1, 10))
    reserved.update("LPT%d" % n for n in range(1, 10))
    if (
        name in {".", ".."}
        or name[-1] in " ."
        or re.search(r'[<>:"/\\|?*]', name)
        or name.split(".", 1)[0].upper() in reserved
    ):
        raise ValidationError("旧服务器名称不是安全的 Windows 目录名：%s" % name)
    return name


def positive_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ValidationError("%s必须为正整数。" % label)
    return value
