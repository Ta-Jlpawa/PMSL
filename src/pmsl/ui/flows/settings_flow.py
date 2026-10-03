"""原设置页的具名动作；存储和资源导入由独立模块负责。"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pmsl.application.settings import SettingsService
from pmsl.domain.errors import PmslError
from pmsl.domain.states import Page
from pmsl.infrastructure.catalog import JsonSettingsStore
from pmsl.infrastructure.user_assets import UserAssets
from pmsl.ui.effects import BackgroundFollower

if TYPE_CHECKING:
    from pmsl.ui.session import UiSession

DEFAULT_FONT = "HarmonyOS_Sans_SC_Bold.ttf"
DEFAULT_BACKGROUND = "bg_theend_re.png"


class SettingsFlow:
    def __init__(self, session: "UiSession") -> None:
        self.session = session
        self.service = SettingsService(JsonSettingsStore(session.storage))
        self.java_test = 0

    def path(self, key: str) -> Path:
        value = getattr(self.service.current, key)
        if value is not None:
            return self.session.paths.inside(value)
        defaults = {
            "console_font": "fonts/" + DEFAULT_FONT,
            "background": "imgs/Background/" + DEFAULT_BACKGROUND,
            "loading_image": "imgs/lg.png",
        }
        return self.session.paths.resource(defaults[key])

    def label(self, key: str) -> str:
        value = getattr(self.service.current, key)
        if value is not None:
            return Path(value).name
        return {
            "console_font": DEFAULT_FONT,
            "console_background": "无",
            "background": DEFAULT_BACKGROUND,
            "loading_image": "lg.png",
        }[key]

    def _background(self, path: Optional[Path] = None) -> BackgroundFollower:
        import pygame

        session = self.session
        target = path or self.path("background")
        try:
            image = session.assets.load_image(target, alpha=False)
            return BackgroundFollower(
                image, (1000, 600), 0.1, self.service.current.dynamic_background
            )
        except (OSError, pygame.error, ValueError) as exc:
            raise PmslError("无法读取背景图片：%s" % target) from exc

    def _import(self, key: str, title: str, extension: str, label: str) -> None:
        session = self.session
        if getattr(self.service.current, key) is not None:
            answer = session.confirm(
                text="请选择资源操作。",
                title=title,
                buttons=["选择文件", "恢复默认", "返回"],
            )
            if answer == "恢复默认":
                background = (
                    self._background(
                        session.paths.resource("imgs/Background/" + DEFAULT_BACKGROUND)
                    )
                    if key == "background"
                    else None
                )
                self.service.update(**{key: None})
                if key == "background":
                    session.background = background
                return
            if answer != "选择文件":
                return
        selected = session.dialogs.choose_file(title, extension, label)
        if selected is None:
            return
        import pygame

        prepared: Optional[BackgroundFollower] = None

        def validate(path: Path) -> None:
            nonlocal prepared
            try:
                if extension == ".ttf":
                    font = pygame.font.Font(str(path), 15)
                    font.render("中文 Minecraft", True, (255, 255, 255))
                elif key == "background":
                    prepared = self._background(path)
                else:
                    pygame.image.load(str(path)).convert_alpha()
            except (OSError, pygame.error, ValueError) as exc:
                raise PmslError("无法读取选择的图片或字体，原设置未修改。") from exc

        importer = UserAssets(session.storage)
        relative = importer.import_file(selected, extension, validate)
        try:
            self.service.update(**{key: relative})
        except BaseException:
            importer.discard(relative)
            raise
        if key == "background":
            assert prepared is not None
            session.background = prepared

    def handle(self, action: str) -> bool:
        session = self.session
        if session.page is Page.HOME and action == "home.settings":
            session.select(Page.PROGRAM_SETTINGS)
            return True
        if session.page not in {Page.PROGRAM_SETTINGS, Page.DISPLAY_SETTINGS, Page.OTHER_SETTINGS}:
            return False
        navigation = {
            "program_settings.home": Page.HOME,
            "program_settings.display-settings": Page.DISPLAY_SETTINGS,
            "display_settings.home": Page.HOME,
            "display_settings.program-settings": Page.PROGRAM_SETTINGS,
            "display_settings.other-settings": Page.OTHER_SETTINGS,
            "other_settings.home": Page.HOME,
            "other_settings.display-settings": Page.DISPLAY_SETTINGS,
        }
        current = self.service.current
        if action in navigation:
            session.select(navigation[action])
        elif action == "program_settings.test-java":
            if (
                session.confirm(
                    text="确定开始运行一次可行性检验吗?",
                    title=session.title,
                    buttons=["开始", "返回"],
                )
                == "开始"
            ):
                session._test_java(session.title)
        elif action == "program_settings.reset-java":
            self.java_test = 0
            session.confirm(text="可行性检验数据文件已重置.", title=session.title, buttons=["明白"])
        elif action == "program_settings.java-path":
            value = session.prompt(
                text="输入 Java 可执行文件路径，或填写“依据系统环境变量”。",
                title=session.title,
                default=current.java or "依据系统环境变量",
            )
            if value is not None:
                configured = None if value.strip() == "依据系统环境变量" else value.strip()
                self.service.update(java=configured)
                self.java_test = 0
                session.java_version = session._java_version()
        elif action == "program_settings.console-font":
            self._import(
                "console_font", "[ 自定义字体 ] 选择一个格式为ttf的字体文件.", ".ttf", "字体文件"
            )
        elif action == "program_settings.console-background":
            self._import(
                "console_background",
                "[ 自定义标示图 ] 选择一个格式为png的图片,建议图片尺寸为1000x600 (10:6).",
                ".png",
                "图片",
            )
        elif action == "display_settings.background":
            self._import(
                "background",
                "[ 自定义标示图 ] 选择一个格式为png的图片,建议图片尺寸为1100x700 (11:7).",
                ".png",
                "图片",
            )
        elif action == "program_settings.external-console":
            if session.server_running:
                session.confirm(
                    text="此设置只能在服务器关闭后修改 !", title=session.title, buttons=["明白"]
                )
            else:
                self.service.update(external_console=not current.external_console)
        elif action == "program_settings.save-log":
            self.service.update(save_server_log=not current.save_server_log)
        elif action == "display_settings.fps":
            self.service.update(fps=30 if current.fps == 60 else 60)
        elif action == "display_settings.dynamic-background":
            self.service.update(dynamic_background=not current.dynamic_background)
            if session.background is not None:
                session.background.enabled = self.service.current.dynamic_background
        elif action not in {
            "program_settings.previous-settings",
            "program_settings.keywords",
            "program_settings.colors",
            "program_settings.console-read-fix",
            "display_settings.interface-style",
            "other_settings.next-settings",
        }:
            raise PmslError("未知设置动作：%s" % action)
        return True
