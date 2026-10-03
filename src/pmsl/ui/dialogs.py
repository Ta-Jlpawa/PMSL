"""复用原 PyMsgBox 外观，并统一管理文件选择器根窗口。"""

import threading
from typing import Any, Optional

from pmsl.domain.errors import PmslError


class Dialogs:
    def __init__(self) -> None:
        self._owner = threading.get_ident()
        self._root: Optional[Any] = None
        self._closed = False

    def _check_thread(self) -> None:
        if threading.get_ident() != self._owner:
            raise PmslError("弹窗只能从界面主线程调用。")
        if self._closed:
            raise PmslError("弹窗管理器已经关闭。")

    def confirm(self, *args: Any, **kwargs: Any) -> Optional[str]:
        self._check_thread()
        import pymsgbox

        return pymsgbox.confirm(*args, **kwargs)

    def prompt(self, *args: Any, **kwargs: Any) -> Optional[str]:
        self._check_thread()
        import pymsgbox

        return pymsgbox.prompt(*args, **kwargs)

    def choose_file(self, title: str, extension: str, label: str) -> Optional[str]:
        self._check_thread()
        import tkinter as tk
        from tkinter import filedialog

        if self._root is None:
            self._root = tk.Tk()
            self._root.withdraw()
        result = filedialog.askopenfilename(
            parent=self._root,
            title=title,
            filetypes=[(label, extension)],
        )
        return str(result) if result else None

    def close(self) -> None:
        if threading.get_ident() != self._owner:
            raise PmslError("弹窗管理器只能从界面主线程关闭。")
        if self._closed:
            return
        if self._root is not None:
            self._root.destroy()
            self._root = None
        self._closed = True


# 仅供过渡业务模块使用，正式页面由 bootstrap 传入 Dialogs。
_default: Optional[Dialogs] = None


def default_dialogs() -> Dialogs:
    global _default
    if _default is None:
        if threading.current_thread() is not threading.main_thread():
            raise PmslError("弹窗管理器必须在主线程首次创建。")
        _default = Dialogs()
    return _default


def confirm(*args: Any, **kwargs: Any) -> Optional[str]:
    return default_dialogs().confirm(*args, **kwargs)


def prompt(*args: Any, **kwargs: Any) -> Optional[str]:
    return default_dialogs().prompt(*args, **kwargs)
