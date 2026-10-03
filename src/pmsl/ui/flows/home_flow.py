"""首页资料与具名管理动作；页面只消费已准备的视图。"""

import io
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Tuple

from pmsl.application.operations import ServerOperations
from pmsl.application.server_browser import BrowserSnapshot, ServerBrowser, server_summary
from pmsl.domain.errors import PmslError
from pmsl.domain.models import ServerProfile
from pmsl.domain.states import Page
from pmsl.domain.validation import validate_legacy_name
from pmsl.infrastructure.server_icons import ServerIcons, encode_icon
from pmsl.ui.models import HomeView

if TYPE_CHECKING:
    from pmsl.ui.session import UiSession


class HomeFlow:
    def __init__(self, session: "UiSession") -> None:
        self.session = session
        self.browser = ServerBrowser()
        self.preferred_id: Optional[str] = None
        self._view = HomeView(0, 0, "无")
        self._default_icon: Any = None
        self._prepared: Optional[Tuple[BrowserSnapshot, HomeView]] = None

    def remember_view(self) -> None:
        self._prepared = self.browser.current, self._view

    def restore_view(self) -> None:
        if self._prepared is not None:
            self.browser.current, self._view = self._prepared

    def _default(self) -> Any:
        if self._default_icon is None:
            import pygame

            payload = encode_icon(self.session.paths.resource("imgs/Background/server_pt.png"))
            self._default_icon = pygame.image.load(io.BytesIO(payload)).convert_alpha()
        return self._default_icon

    def on_enter(self) -> None:
        session = self.session
        previous = self.browser.current
        try:
            self.browser.refresh(session.server_profiles(), self.preferred_id)
            current = self.browser.current
            view = HomeView(len(current.profiles), current.index, session.java_version)
            profile = current.selected
            if profile is not None and len(current.profiles) <= 99:
                path = session.layout.file(profile, "icon.png")
                icon = session.assets.load_image(path) if path.is_file() else self._default()
                view = replace(
                    view,
                    name=profile.name,
                    summary=server_summary(profile),
                    icon=icon,
                    server_id=profile.id,
                )
        except BaseException:
            self.browser.current = previous
            raise
        self._view, self.preferred_id = view, None

    def view(self) -> HomeView:
        return replace(self._view, java_version=self.session.java_version)

    def _profile(self) -> ServerProfile:
        selected = self.browser.current.selected
        if selected is None or len(self.browser.current.profiles) > 99:
            raise PmslError("当前页面没有可管理的服务器。")
        profile = self.session.store.get(selected.id)
        self.session.layout.validate(profile)
        return profile

    def _manage(self, action: str, profile: ServerProfile) -> None:
        session = self.session
        snapshot = session.runtime.update()
        if snapshot is not None and snapshot.active:
            raise PmslError("服务器正在运行，停服后才能删除或重命名。")
        operations = ServerOperations(session.storage)
        if action == "home.rename":
            name = session.prompt(
                text="请输入想要重命名的名称.", title=session.title, default=profile.name
            )
            if name is None:
                return
            validate_legacy_name(name)
            if (
                session.confirm(
                    text="确定要将服务器 [%s] 重命名为 [%s] 吗?" % (profile.name, name),
                    title=session.title,
                    buttons=["确定", "取消"],
                )
                != "确定"
            ):
                return
            operations.rename(profile.id, name)
        else:
            if (
                session.confirm(
                    text="你是否移除服务器 %s ?.\n服务器文件将移入程序内回收区。" % profile.name,
                    title=session.title,
                    buttons=["暂不移除", "确定"],
                )
                != "确定"
            ):
                return
            if (
                session.confirm(
                    text="你真的想要移除服务器 %s 吗?." % profile.name,
                    title=session.title,
                    buttons=["暂不移除", "我真的确定!!"],
                )
                != "我真的确定!!"
            ):
                return
            operations.trash(profile.id)
        session.select(Page.HOME)

    def _icon(self, profile: ServerProfile) -> None:
        import pygame

        session = self.session
        selected = session.dialogs.choose_file(
            "[ 自定义标示图 ] 选择一个格式为png的图片,建议图片尺寸为215x397 (1:1.85).",
            ".png",
            "图片",
        )
        if selected is None:
            return
        source = Path(selected)
        payload = encode_icon(source)
        # 解码及场景资源均在替换前准备，失败时保留原文件和原画面。
        prepared = pygame.image.load(io.BytesIO(payload)).convert_alpha()
        target = ServerIcons(session.storage).save(profile.id, payload)
        session.assets.invalidate_image(target)
        self._view = replace(self._view, icon=prepared)

    def _create(self) -> None:
        session = self.session
        pending = session.creation.pending()
        if pending:
            task_id, document = pending[0]
            name = document.get("spec", {}).get("name", task_id)
            answer = session.confirm(
                text="发现未完成的创建任务：%s" % name,
                title=session.title,
                buttons=["继续上次创建", "新建", "返回"],
            )
            if answer == "继续上次创建":
                session.creation.resume(task_id)
                return
            if answer != "新建":
                return
        if len(session._server_names()) >= 99:
            raise PmslError("创建的服务器过多（最多99个）。")
        if session.settings.java_test in {0, 2}:
            answer = session.confirm(
                text="在开设服务器之前,非常建议运行一次可行性检验!\n否则程序有可能因为个人配置而报错!"
                if session.settings.java_test == 0
                else "上次可行性检验未通过,是否开始重检测?\n请确保你的错误已修复!",
                title=session.title,
                buttons=["开始", "跳过", "返回"],
            )
            if answer == "开始":
                session._test_java(session.title)
                return
            if answer != "跳过":
                return
            session.settings.java_test = 1
            session.confirm(
                text="你可以在‘程序设置’中进行检验数据重置或重检验.",
                title=session.title,
                buttons=["明白"],
            )
        session.creation.reset()
        session.select(Page.CREATE_TYPE)
        return

    def handle(self, action: str) -> bool:
        session = self.session
        if (session.page, action) in {
            (Page.ABOUT, "about.home"),
            (Page.CONSOLE, "console.hide-console"),
        }:
            console = session.console if session.page is Page.CONSOLE else None
            session.select(Page.HOME)
            if console is not None:
                console.hide()
            return True
        if session.page is not Page.HOME:
            return False
        if action == "home.create":
            self._create()
        elif action == "home.about":
            session.select(Page.ABOUT)
        elif action in {"home.previous-server", "home.next-server"}:
            previous = self.browser.current
            self.browser.move(-1 if action == "home.previous-server" else 1)
            try:
                session.select(Page.HOME)
            except BaseException:
                self.browser.current = previous
                raise
        elif action == "home.console":
            snapshot = session.runtime.update()
            console = session.console
            if snapshot is not None and snapshot.active and console is not None:
                session.select(Page.CONSOLE)
                console.show()
        elif action == "home.start":
            session._start_server(self._profile())
        elif action in {"home.rename", "home.delete"}:
            self._manage(action, self._profile())
        elif action == "home.icon":
            self._icon(self._profile())
        else:
            return False
        return True
