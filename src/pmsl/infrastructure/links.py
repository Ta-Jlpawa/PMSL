"""按预定义名称打开作者页面和项目链接。"""

import webbrowser

from pmsl.domain.errors import PmslError

LINKS = {
    "author": "https://space.bilibili.com/1101301178",
    "github": "https://github.com/Ta-Jlpawa/PMSL",
    "eula": "https://www.minecraft.net/zh-hans/eula",
}


def open_link(name: str) -> None:
    if name not in LINKS:
        raise PmslError("未知界面链接。")
    if not webbrowser.open(LINKS[name]):
        raise PmslError("无法打开系统浏览器，请检查浏览器配置。")
