"""显式安装自检：准备完整界面会话，不启动服务器或探测 Java。"""

import json
import os
import ssl
import sys
import tempfile
import time
from typing import Any, Dict

from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.paths import AppPaths


def verify_installation(paths: AppPaths, headless: bool = True) -> int:
    started = time.monotonic()
    report: Dict[str, Any] = dict(schema_version=1, status="failed")
    previous = {name: os.environ.get(name) for name in ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER")}
    try:
        import tkinter

        import pygame
        import pymsgbox

        from pmsl.domain.states import Page
        from pmsl.infrastructure.storage import InstanceLock, JsonStorage
        from pmsl.ui.app import App
        from pmsl.ui.assets import Assets
        from pmsl.ui.dialogs import Dialogs
        from pmsl.ui.resources import FONT_SIZES, IMAGE_FILES
        from pmsl.ui.session import UiSession

        runtime = paths.bundled(".")
        temporary = paths.data("tmp")
        if paths.inside(tempfile.gettempdir()) != temporary:
            raise ValueError("运行临时目录未限定在程序目录内。")
        os.environ.update(
            SDL_VIDEODRIVER="dummy" if headless else "windows", SDL_AUDIODRIVER="dummy"
        )
        pygame.init()
        assets = Assets(paths)
        dialogs = Dialogs()
        session = None
        app = None
        pages = []
        try:
            surface = pygame.display.set_mode((1000, 600))
            video_driver = pygame.display.get_driver()
            with InstanceLock(paths) as lock:
                session = UiSession(
                    paths,
                    assets,
                    dialogs,
                    surface,
                    java_version="无",
                    storage=JsonStorage(paths, lock),
                )
                app = App(surface, session)
                for page in Page:
                    session.select(page)
                    app.update(0.0)
                    app.render()
                    pygame.display.update()
                    pages.append(page.value)
                    if not headless:
                        pygame.event.pump()
                        pygame.time.wait(30)
                for size in FONT_SIZES:
                    session.visuals.font(size).render("中文服务器 English", True, (255, 255, 255))
                session.select(Page.HOME)
                app.update(0.0)
                app.render()
                if not headless:
                    screen = paths.data("diagnostics/home.png")
                    screen.parent.mkdir(parents=True, exist_ok=True)
                    pygame.image.save(surface, str(screen))
                    if (
                        dialogs.confirm(
                            text="PMSL 本机确认框检查",
                            title="安装检查",
                            buttons=["继续", "返回"],
                            timeout=500,
                        )
                        != pymsgbox.TIMEOUT_RETURN_VALUE
                    ):
                        raise ValueError("确认框的超时返回不正确。")
                    if (
                        dialogs.prompt(
                            text="PMSL 本机输入框检查",
                            title="安装检查",
                            default="中文输入",
                            timeout=500,
                        )
                        != pymsgbox.TIMEOUT_RETURN_VALUE
                    ):
                        raise ValueError("输入框的超时返回不正确。")
                    root = tkinter.Tk()
                    try:
                        root.withdraw()
                        root.update_idletasks()
                    finally:
                        root.destroy()
                app.handle_event(pygame.event.Event(pygame.QUIT))
                if app.running:
                    raise ValueError("空闲主界面未能正常退出。")
        finally:
            if app is not None:
                app.close()
            if session is not None:
                session.close()
            dialogs.close()
            assets.clear()
            pygame.quit()
        context = ssl.create_default_context()
        text = "中文路径和命令"
        if text.encode("cp936").decode("cp936") != text:
            raise ValueError("中文编码不可用。")
        tcl = tkinter.Tcl()
        report.update(
            status="passed",
            frozen=bool(getattr(sys, "frozen", False)),
            program_dir=str(paths.program_dir),
            runtime_dir=str(runtime),
            temporary_dir=str(temporary),
            python=sys.version,
            images=len(IMAGE_FILES),
            pages=pages,
            creation_tips_loaded=True,
            video_driver=video_driver,
            native_dialogs_checked=not headless,
            font_sizes=list(FONT_SIZES),
            pygame=pygame.version.ver,
            pymsgbox=pymsgbox.__name__,
            tcl=str(tcl.call("info", "patchlevel")),
            openssl=ssl.OPENSSL_VERSION,
            ssl_verify_mode=int(context.verify_mode),
            unicode_encoding="cp936",
        )
    except Exception as exc:
        # 自检保留异常信息，正常业务仍按自己的错误边界处理。
        report["error"] = "%s: %s" % (type(exc).__name__, exc)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    report["seconds"] = round(time.monotonic() - started, 3)
    destination = paths.data("diagnostics/installation.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(
        paths, destination, json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
    )
    return 0 if report["status"] == "passed" else 1
