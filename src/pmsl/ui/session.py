"""组装界面服务和资源，协调页面流程、后台任务、弹窗及退出清理。"""

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pmsl import __version__
from pmsl.application.runtime import ServerRuntime
from pmsl.domain.errors import PmslError
from pmsl.domain.models import ServerProfile
from pmsl.domain.states import Page
from pmsl.infrastructure.catalog import JsonServerStore
from pmsl.infrastructure.java import JavaDetector
from pmsl.infrastructure.links import open_link
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.preparation import profile_launch_plan
from pmsl.infrastructure.server_layout import ServerLayout
from pmsl.infrastructure.storage import JsonStorage
from pmsl.infrastructure.version_catalog import DownloadSourcesStore, VersionCatalogStore
from pmsl.ui.assets import Assets
from pmsl.ui.console import ConsolePresenter
from pmsl.ui.dialogs import Dialogs
from pmsl.ui.effects import BackgroundFollower, ImageAnimation
from pmsl.ui.flows.creation_flow import CreationFlow
from pmsl.ui.flows.home_flow import HomeFlow
from pmsl.ui.flows.properties_flow import PropertiesFlow
from pmsl.ui.flows.settings_flow import SettingsFlow
from pmsl.ui.models import CreationView, HomeView, PropertiesView, SettingsView
from pmsl.ui.scene_builder import Visuals


@dataclass
class DialogRequest:
    kind: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    done: threading.Event = field(default_factory=threading.Event)
    result: Optional[str] = None
    error: Optional[BaseException] = None


class UiSession:
    def __init__(
        self,
        paths: AppPaths,
        assets: Assets,
        dialogs: Dialogs,
        surface: Any,
        java_version: Optional[str] = None,
        runtime: Optional[ServerRuntime] = None,
        storage: Optional[JsonStorage] = None,
    ) -> None:
        self.paths = paths
        self.assets = assets
        self.dialogs = dialogs
        self.runtime = runtime if runtime is not None else ServerRuntime(paths)
        self.storage = storage if storage is not None else JsonStorage(paths)
        self.store = JsonServerStore(self.storage)
        self.layout = ServerLayout(paths)
        self.versions = VersionCatalogStore(self.storage).load()
        self.download_templates = DownloadSourcesStore(self.storage).load()
        self.creation = CreationFlow(self)
        self.settings = SettingsFlow(self)
        self.properties = PropertiesFlow(self)
        self.home = HomeFlow(self)
        self._exit_pending = False
        self._next_stop_prompt = 0.0
        self._finished_task: Optional[str] = None
        self.java_version: str = java_version if java_version is not None else "无"
        self.owner = threading.get_ident()
        self.closed = False
        self.requests: queue.Queue[DialogRequest] = queue.Queue()
        self._request_lock = threading.Lock()
        self._revision = 0
        self._page = Page.HOME
        self._prepared_page: Optional[Page] = None
        self._prepared_console: Optional[Tuple[ConsolePresenter, bool]] = None
        self.console: Optional[ConsolePresenter] = None
        self.animation: Optional[ImageAnimation] = None
        self.background: Optional[BackgroundFollower] = None
        self.server_running = False
        self.running_name = ""
        self.surface = surface
        try:
            self._initialize(java_version)
        except BaseException:
            self.close()
            raise

    def _dialog(self, kind: str, *args: Any, **kwargs: Any) -> Optional[str]:
        if self.closed:
            raise PmslError("界面已经关闭，无法显示任务弹窗。")
        if threading.get_ident() == self.owner:
            return getattr(self.dialogs, kind)(*args, **kwargs)
        request = DialogRequest(kind, args, kwargs)
        with self._request_lock:
            if self.closed:
                raise PmslError("界面已经关闭，无法显示任务弹窗。")
            self.requests.put(request)
        request.done.wait()
        if request.error is not None:
            raise request.error
        return request.result

    def confirm(self, *args: Any, **kwargs: Any) -> Optional[str]:
        return self._dialog("confirm", *args, **kwargs)

    def prompt(self, *args: Any, **kwargs: Any) -> Optional[str]:
        return self._dialog("prompt", *args, **kwargs)

    def _configured_java(self) -> Optional[str]:
        return self.settings.service.current.java

    def _java_version(self) -> str:
        try:
            return str(JavaDetector(self.paths).detect(self._configured_java()).major)
        except PmslError:
            return "无"

    def _test_java(self, version: str) -> None:
        try:
            info = JavaDetector(self.paths).detect(self._configured_java())
        except PmslError as exc:
            self.settings.java_test = 2
            self.confirm(text=str(exc), title=version, buttons=["返回"])
            return
        self.settings.java_test = 1
        self.java_version = str(info.major)
        self.confirm(
            text="Java %s 可正常运行。\n%s" % (info.version, info.executable),
            title=version,
            buttons=["继续"],
        )

    def _initialize(self, java_version: Optional[str]) -> None:
        import pygame

        self._title = "PMSL " + __version__
        self._clock: Any = pygame.time.Clock()
        self.java_version = java_version if java_version is not None else self._java_version()
        if java_version is not None:
            self.settings.java_test = 1
        self.visuals = Visuals(self.assets)
        self.background = self.settings._background()
        self.select(Page.HOME)

    @property
    def page(self) -> Page:
        return self._page

    @property
    def fps(self) -> int:
        return self.settings.service.current.fps

    @property
    def external_console(self) -> bool:
        return self.settings.service.current.external_console

    @property
    def clock(self) -> Any:
        return self._clock

    @property
    def title(self) -> str:
        return self._title

    @property
    def busy(self) -> bool:
        return self.creation.busy or self.server_running

    @property
    def revision(self) -> int:
        return self._revision

    def invalidate(self) -> None:
        self._revision += 1

    def server_profiles(self) -> Tuple[ServerProfile, ...]:
        profiles = tuple(self.store.list())
        for profile in profiles:
            self.layout.validate(profile)
        if len({profile.name.casefold() for profile in profiles}) != len(profiles):
            raise PmslError("目录包含重复显示名称，不能继续管理。")
        return profiles

    def _server_names(self) -> List[str]:
        return [profile.name for profile in self.server_profiles()]

    def home_view(self) -> HomeView:
        return self.home.view()

    def settings_view(self) -> SettingsView:
        current = self.settings.service.current
        return SettingsView(
            self.fps,
            self.external_console,
            self.settings.service.current.dynamic_background,
            self.settings.label("console_font"),
            self.settings.label("console_background"),
            self.settings.label("background"),
            current.java or "依据系统环境变量",
            current.save_server_log,
        )

    def creation_view(self) -> CreationView:
        return self.creation.view()

    def properties_view(self) -> PropertiesView:
        return self.properties.view()

    def select(self, page: Page) -> None:
        if not isinstance(page, Page):
            raise PmslError("页面必须使用具名 Page。")
        previous = self._page
        self._page = page
        try:
            if page is Page.HOME:
                self.home.on_enter()
            self.creation.on_enter(page)
            if page in {Page.WORLD_PROPERTIES, Page.SERVER_PROPERTIES}:
                self.properties.on_enter()
        except BaseException:
            self._page = previous
            raise
        self.invalidate()

    def remember_view(self) -> None:
        self._prepared_page = self.page
        self.properties.remember_view()
        self.home.remember_view()
        self._prepared_console = (
            (self.console, self.console.is_visible()) if self.console is not None else None
        )

    def restore_view(self) -> None:
        if self._prepared_page is not None:
            self._page = self._prepared_page
            self.invalidate()
            self.properties.restore_view()
            self.home.restore_view()
            if self._prepared_console is not None:
                console, visible = self._prepared_console
                if self.console is console:
                    (console.show if visible else console.hide)()

    def perform(self, action: str) -> None:
        if self.closed:
            return
        for flow in (self.home, self.properties, self.settings, self.creation):
            if flow.handle(action):
                self.invalidate()
                return
        if self.page is Page.ABOUT and action in {"about.author-link", "about.github-link"}:
            self.open_link("author" if action == "about.author-link" else "github")
            return
        raise PmslError("动作不属于当前页面或尚未实现：%s" % action)

    def open_link(self, name: str) -> None:
        open_link(name)

    def _start_server(self, profile: ServerProfile) -> None:
        snapshot = self.runtime.update()
        if snapshot is not None and snapshot.active:
            raise PmslError("已有服务器正在运行，请先在控制台输入 stop 正常停服。")
        if (
            self.confirm(
                text="你是否确定启动服务器 " + profile.name + " ?.",
                title=self.title,
                buttons=["暂不启动", "确定"],
            )
            != "确定"
        ):
            return
        profile = self.store.get(profile.id)
        self.layout.validate(profile)
        plan = profile_launch_plan(
            self.paths,
            profile.directory,
            profile.memory_gib,
            profile.java or self._configured_java(),
            self.external_console,
        )
        console = None
        if not plan.external_console:
            settings = self.settings.service.current
            font = self.assets.load_font(self.settings.path("console_font"), 15)
            background = (
                None
                if settings.console_background is None
                else self.assets.load_image(self.settings.path("console_background"))
            )
            console = ConsolePresenter(
                font, self.runtime.logs, self.runtime.send_command, background
            )
        animation = None
        if not plan.external_console:
            animation = ImageAnimation(self.visuals.image("running_list"), (500, 615), (500, 585))
        save_log = self.settings.service.current.save_server_log
        self.runtime.start(profile.id, profile.name, plan, save_log)
        self.running_name, self.server_running, self.console = profile.name, True, console
        self.animation = animation
        if animation is not None:
            animation.start()
        self.invalidate()

    @property
    def should_exit(self) -> bool:
        return self._exit_pending and not self.busy

    def request_exit(self) -> bool:
        snapshot = self.runtime.update()
        if snapshot is not None and snapshot.active:
            answer = self.confirm(
                text="服务器仍在运行，请选择退出方式。",
                title=self.title,
                buttons=["等待结束后退出", "停服并退出", "返回程序"],
            )
            if answer in {"等待结束后退出", "停服并退出"}:
                if answer == "停服并退出":
                    self.runtime.request_stop()
                self._exit_pending = True
            else:
                self._exit_pending = False
            return False
        if self.busy:
            if self.creation.busy:
                answer = self.confirm(
                    text="创建任务仍在运行，请选择退出方式。",
                    title=self.title,
                    buttons=["取消任务并退出", "等待结束后退出", "返回程序"],
                )
                if answer in {"取消任务并退出", "等待结束后退出"}:
                    if answer == "取消任务并退出" and self.creation.task is not None:
                        self.creation.task.cancel()
                    self._exit_pending = True
                return False
            self.confirm(
                text="创建或下载任务仍在运行，请先完成或取消任务后再退出。",
                title=self.title,
                buttons=["返回程序"],
            )
            return False
        return True

    def update(self) -> None:
        self.creation.update()
        for _ in range(8):
            try:
                request = self.requests.get_nowait()
            except queue.Empty:
                break
            try:
                request.result = getattr(self.dialogs, request.kind)(
                    *request.args, **request.kwargs
                )
            except BaseException as exc:
                request.error = exc
            finally:
                request.done.set()
        console = self.console
        if console is not None:
            console.update_output()
        snapshot = self.runtime.update()
        if snapshot is not None:
            self.server_running = snapshot.active
            if snapshot.stop_timed_out and time.monotonic() >= self._next_stop_prompt:
                answer = self.confirm(
                    text="正常停服已等待30秒，服务器仍在运行。强制终止可能使尚未保存的世界数据丢失。",
                    title=self.title,
                    buttons=["继续等待", "强制终止", "取消退出"],
                )
                self._next_stop_prompt = time.monotonic() + 30
                if answer == "强制终止":
                    self.runtime.force_stop()
                elif answer == "取消退出":
                    self._exit_pending = False
            if not snapshot.active and self._finished_task != snapshot.task_id:
                self._finished_task = snapshot.task_id
                logs = self.runtime.logs().lines
                last = snapshot.error or (logs[-1] if logs else "由于优化机制,未能获取日志")
                if not self._exit_pending:
                    self.confirm(
                        text="服务器已关闭! \n点击按钮后程序会自动关闭cmd进程并跳转至主界面\n"
                        + last,
                        title=self.title,
                        buttons=["关闭进程"],
                    )
                if console is not None:
                    console.hide()
                if self.animation is not None:
                    self.animation.stop()
                self.console, self.animation, self.server_running = None, None, False
                self._prepared_console = None
                self.select(Page.HOME)

    def handle_console_event(self, event: Any) -> None:
        if self.console is not None and self.page is Page.CONSOLE:
            self.console.handle_event(event)

    def draw_background(self, target: Any) -> None:
        import pygame

        target.fill((27, 27, 27))
        if self.background is not None:
            self.background.update(tuple(pygame.mouse.get_pos()))
            self.background.render(target)

    def draw_overlays(self, target: Any) -> None:
        if self.console is not None and self.console.is_visible():
            target.blit(self.console.render(), (0, 0))
        if self.animation is not None:
            self.animation.render(target)
        if self.server_running and not self.external_console:
            target.blit(
                self.visuals.text(self.running_name + "  正在运行中...", 15, (0, 255, 0), True),
                (10, 570),
            )
        footer = "%s   By TA_JLPawa / FPS: %.2f" % (self.title, self.clock.get_fps())
        target.blit(self.visuals.text(footer, 10, (255, 255, 255), True), (10, 585))

    def close(self) -> None:
        with self._request_lock:
            if self.closed:
                return
            self.closed = True
            while True:
                try:
                    request = self.requests.get_nowait()
                except queue.Empty:
                    break
                request.error = PmslError("界面已经关闭。")
                request.done.set()
        try:
            self.creation.close()
        finally:
            try:
                self.runtime.close()
            finally:
                if self.animation is not None:
                    self.animation.stop()
                self._prepared_console, self._prepared_page = None, None
                self.console, self.animation, self.background = None, None, None
