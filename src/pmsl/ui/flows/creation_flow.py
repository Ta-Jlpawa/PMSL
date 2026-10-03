"""现有八步向导的任务适配；草稿只存在于本会话。"""

import random
import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple
from uuid import uuid4

from pmsl.application.creation import CreationTask
from pmsl.application.creation_editor import CreationEditor
from pmsl.application.operations import ServerOperations
from pmsl.domain.creation import CreationSnapshot, CreationSpec
from pmsl.domain.errors import PmslError
from pmsl.domain.models import CoreSelection
from pmsl.domain.states import CreationState, Page
from pmsl.domain.validation import positive_integer, validate_legacy_name
from pmsl.domain.versions import CreationInput
from pmsl.infrastructure.creation_text import CreationText
from pmsl.infrastructure.downloads import Downloader, MetadataClient
from pmsl.infrastructure.preparation import Preparer
from pmsl.infrastructure.providers import CoreProviders
from pmsl.ui.models import CreationView, VersionListView

if TYPE_CHECKING:
    from pmsl.ui.session import UiSession


class CreationFlow:
    def __init__(self, session: "UiSession") -> None:
        self.session = session
        self.editor = CreationEditor(session.versions)
        self.task: Optional[CreationTask] = None
        self._observed: Optional[CreationSnapshot] = None
        self._display: Optional[CreationSnapshot] = None
        self.text = CreationText(session.paths)
        self._tips = self.text.tips()
        self._tip_lines: Tuple[str, ...] = ("Tip:  点击此处框框范围内,可以随机切换Tip语句哦!",)
        self._eula_lines: tuple = ()
        self._eula_task: Optional[str] = None
        self._eula_error: Optional[str] = None
        self._progress_image: Any = None
        self._last_progress = 0.0
        self._pages: Dict[str, int] = {}

    @staticmethod
    def defaults() -> Dict[str, Any]:
        return dict(
            core="Paper",
            core_version=["307"],
            mc_version="1.19.2",
            run_memory="4",
            server_name="NewServer_1",
            downloaded="0",
            first_start="0",
        )

    @property
    def raw(self) -> Dict[str, Any]:
        current = self.editor.current
        selection = current.selection
        return dict(
            core=selection.core,
            core_version=[selection.loader, selection.installer]
            if selection.core == "Fabric"
            else [selection.build or "none"],
            mc_version=selection.minecraft_version,
            run_memory=str(current.memory_gib),
            server_name=current.name,
            downloaded=str(
                int(
                    self._display is not None
                    and self._display.state
                    in {
                        CreationState.DOWNLOADED,
                        CreationState.PREPARING,
                        CreationState.WAITING_FOR_EULA,
                        CreationState.COMMITTING,
                        CreationState.COMPLETED,
                    }
                )
            ),
            first_start=str(
                int(
                    self._display is not None
                    and self._display.state
                    in {
                        CreationState.WAITING_FOR_EULA,
                        CreationState.COMMITTING,
                        CreationState.COMPLETED,
                    }
                )
            ),
        )

    @raw.setter
    def raw(self, raw: Dict[str, Any]) -> None:
        versions = raw["core_version"]
        core = raw["core"]
        if not isinstance(versions, list) or len(versions) != (2 if core == "Fabric" else 1):
            raise PmslError("核心选择字段不完整。")
        selection = CoreSelection(
            core,
            raw["mc_version"],
            versions[0] if core in {"Paper", "Forge"} else None,
            versions[0] if core == "Fabric" else None,
            versions[1] if core == "Fabric" else None,
        )
        self.editor.replace_input(
            CreationInput(raw["server_name"], selection, int(raw["run_memory"]))
        )

    def pending(self) -> list:
        return CreationTask.pending(self.session.storage)

    def resume(self, task_id: str) -> None:
        if self.busy:
            raise PmslError("当前创建任务尚未结束。")
        paths = self.session.paths
        task = CreationTask.restore(
            self.session.storage, task_id, self._providers(), Downloader(paths), Preparer(paths)
        )
        if self.task is not None:
            self.task.close()
        self.editor.replace_input(
            CreationInput(task.spec.name, task.spec.selection, task.spec.memory_gib)
        )
        self.editor.kind = "模组服" if task.spec.selection.core in {"Fabric", "Forge"} else "插件服"
        self.task, self._observed = task, None
        self._eula_task, self._eula_error = None, None
        self._eula_lines = ()
        state = task.snapshot().state
        self.session.select(
            Page.CREATE_FINISH
            if state is CreationState.COMMITTING
            else Page.CREATE_EULA
            if state is CreationState.WAITING_FOR_EULA
            else Page.CREATE_DOWNLOAD
        )
        self.update()

    def reset(self) -> None:
        self._invalidate()
        self.editor = CreationEditor(self.session.versions)
        names = {name.casefold() for name in self.session._server_names()}
        number = len(names) + 1
        while ("NewServer_%d" % number).casefold() in names:
            number += 1
        self.editor.name("NewServer_%d" % number)
        self._pages.clear()

    @property
    def busy(self) -> bool:
        return self.task is not None and self.task.busy

    def _invalidate(self) -> None:
        if self.busy:
            raise PmslError("创建任务仍在释放资源，不能修改输入。")
        if self.task is not None:
            self.task.close()
        self.task, self._observed = None, None
        self._display, self._eula_task = None, None
        self._eula_lines = ()
        self._eula_error = None

    def write(self, key: str, value: Any) -> None:
        if self.busy:
            raise PmslError("创建任务仍在释放资源，不能修改输入。")
        previous = self.editor.current
        if key == "server_name":
            validate_legacy_name(value)
            if any(name.casefold() == value.casefold() for name in self.session._server_names()):
                raise PmslError("目标服务器名称已存在。")
            self.editor.name(value)
        elif key == "run_memory":
            try:
                self.editor.memory(int(value))
            except (TypeError, ValueError) as exc:
                raise PmslError("运行内存必须为正整数。") from exc
        elif key == "core":
            self.editor.choose_core(value)
        elif key == "mc_version":
            self.editor.choose_game(value)
        elif key == "core_version":
            raw = self.raw
            raw[key] = value
            self.raw = raw
        else:
            raise PmslError("未知或无效的创建字段：%s" % key)
        if self.editor.current != previous:
            self._invalidate()

    def _new_task(self) -> CreationTask:
        current = self.editor.current
        selection = self.editor.validate()
        spec = CreationSpec(uuid4().hex, current.name, selection, current.memory_gib)
        if len(self.session._server_names()) >= 99:
            raise PmslError("创建的服务器过多（最多99个）。")
        paths = self.session.paths
        return CreationTask(paths, spec, self._providers(), Downloader(paths), Preparer(paths))

    def _providers(self) -> CoreProviders:
        codes = {
            game.version + ":" + build.version: build.paper_code
            for game in self.session.versions.games
            for build in game.builds
            if build.paper_code is not None
        }
        return CoreProviders(
            MetadataClient(self.session.paths), self.session.download_templates, codes
        )

    def on_enter(self, page: Page) -> None:
        if page is Page.CREATE_GAME_VERSION:
            self._pages["game"] = 0
        elif page is Page.CREATE_CORE_VERSION:
            self._pages.update(build=0, loader=0, installer=0)
        if page in {Page.CREATE_DOWNLOAD, Page.CREATE_EULA, Page.CREATE_FINISH}:
            self._display = self._snapshot()
        if page is Page.CREATE_DOWNLOAD:
            self._tip_lines = ("Tip:  点击此处框框范围内,可以随机切换Tip语句哦!",)
            self._progress_image = None
            if self.session.settings.service.current.loading_image is not None:
                self._progress_image = self.session.assets.load_image(
                    self.session.settings.path("loading_image"), (770, 20)
                )
        if (
            page is Page.CREATE_EULA
            and self._display is not None
            and self._display.state in {CreationState.WAITING_FOR_EULA, CreationState.COMMITTING}
            and self._eula_task != self._display.task_id
        ):
            self._read_eula()

    def _snapshot(self) -> Optional[CreationSnapshot]:
        if self.task is None:
            return None
        snapshot = self.task.snapshot()
        return snapshot if snapshot.task_id == self.task.spec.task_id else None

    def _read_eula(self) -> bool:
        if self.task is None:
            raise PmslError("尚无当前创建任务。")
        self._eula_lines = ()
        self._eula_task = self.task.spec.task_id
        self._eula_error = None
        try:
            self._eula_lines = self.text.eula(str(self.task.server_dir))
            if not self._eula_lines:
                self._eula_error = "EULA 文件为空，请重新初始化。"
            return bool(self._eula_lines)
        except PmslError as exc:
            self._eula_error = str(exc)
            return False
        finally:
            self.session.invalidate()

    def _values(self, component: str) -> tuple:
        selection = self.editor.current.selection
        if component == "game":
            return self.session.versions.versions(selection.core)
        if component == "build":
            return tuple(
                build.version
                for build in self.session.versions.release(
                    selection.core, selection.minecraft_version
                ).builds
            )
        if component == "loader":
            return self.session.versions.fabric_loaders
        if component == "installer":
            return self.session.versions.fabric_installers
        raise PmslError("未知版本列表。")

    def view(self) -> CreationView:
        components = (
            ("game",)
            if self.session.page is Page.CREATE_GAME_VERSION
            else (
                ("loader", "installer")
                if self.editor.current.selection.core == "Fabric"
                else ("build",)
                if self.editor.current.selection.core != "Spigot"
                else ()
            )
            if self.session.page is Page.CREATE_CORE_VERSION
            else ()
        )
        lists = []
        for component in components:
            values = self._values(component)
            size = 3 if component in {"loader", "installer"} else 7
            count = max(1, (len(values) + size - 1) // size)
            page = min(self._pages.get(component, 0), count - 1)
            lists.append(
                VersionListView(component, values[page * size : (page + 1) * size], page, count)
            )
        current = self.editor.current
        if (
            self.session.page in {Page.CREATE_DOWNLOAD, Page.CREATE_EULA, Page.CREATE_FINISH}
            and self.task is not None
        ):
            spec = self.task.spec
            current = CreationInput(spec.name, spec.selection, spec.memory_gib)
        return CreationView(
            current,
            self.editor.kind,
            tuple(lists),
            self._display,
            self.busy,
            self._eula_lines,
            self._tip_lines,
            self._progress_image,
            self._display is not None
            and self._eula_task == self._display.task_id
            and bool(self._eula_lines),
            self._eula_error,
        )

    def _edit_action(self, action: str) -> bool:
        page = self.session.page
        pages = (
            Page.CREATE_TYPE,
            Page.CREATE_CORE,
            Page.CREATE_GAME_VERSION,
            Page.CREATE_CORE_VERSION,
            Page.CREATE_SETTINGS,
        )
        if page not in pages:
            return False
        if self.busy:
            raise PmslError("请等待当前创建任务结束后再修改选择。")
        prefix = page.value + "."
        if not action.startswith(prefix):
            raise PmslError("创建动作不属于当前页面。")
        name = action[len(prefix) :]
        previous = self.editor.current
        if name == "home" and page is Page.CREATE_TYPE:
            self.session.select(Page.HOME)
        elif name == "back" and page is not Page.CREATE_TYPE:
            self.session.select(pages[pages.index(page) - 1])
        elif name == "next":
            if page in {Page.CREATE_GAME_VERSION, Page.CREATE_CORE_VERSION, Page.CREATE_SETTINGS}:
                self.editor.validate()
            self.session.select(
                pages[pages.index(page) + 1]
                if page is not Page.CREATE_SETTINGS
                else Page.CREATE_DOWNLOAD
            )
        elif page is Page.CREATE_TYPE and name in {"plugin", "mod"}:
            self.editor.set_kind("插件服" if name == "plugin" else "模组服")
        elif page is Page.CREATE_CORE and name in {"first-core", "second-core"}:
            cores = ("Spigot", "Paper") if self.editor.kind == "插件服" else ("Fabric", "Forge")
            self.editor.choose_core(cores[0 if name == "first-core" else 1])
        elif name.startswith(("previous-", "next-")) and name.endswith("-page"):
            component = name.split("-")[1]
            component = {"version": "game", "core": "build"}.get(component, component)
            if component not in {listing.component for listing in self.view().lists}:
                raise PmslError("此页面没有该版本列表。")
            size = 3 if component in {"loader", "installer"} else 7
            count = max(1, (len(self._values(component)) + size - 1) // size)
            current = self._pages.get(component, 0)
            self._pages[component] = max(
                0, min(count - 1, current + (-1 if name.startswith("previous-") else 1))
            )
        elif name.startswith("select-") and ":" in name:
            component, selected_version = name[7:].split(":", 1)
            if not any(
                listing.component == component and selected_version in listing.values
                for listing in self.view().lists
            ):
                raise PmslError("该选择不属于当前版本页面。")
            if component == "game":
                self.editor.choose_game(selected_version)
            else:
                self.editor.choose_component(component, selected_version)
        elif page is Page.CREATE_SETTINGS and name in {"memory", "name"}:
            if name == "memory":
                value = self.session.prompt(
                    text="输入你想开设的服务器运行内存(输入正整数,单位:G).",
                    title=self.session.title,
                    default=str(self.editor.current.memory_gib),
                )
                if value is not None:
                    number = int(value)
                    positive_integer(number, "运行内存")
                    if (
                        number < 12
                        or self.session.confirm(
                            text="我的天啊,你真的想要用这么巨大的内存开一个小小的MC服务器?",
                            title=self.session.title,
                            buttons=["让我访问!", "我放弃"],
                        )
                        == "让我访问!"
                    ):
                        self.write("run_memory", value)
            else:
                value = self.session.prompt(
                    text="输入你想设置的服务器名称.(建议为全英文)",
                    title=self.session.title,
                    default=self.editor.current.name,
                )
                if value is not None:
                    self.write("server_name", value)
        else:
            raise PmslError("未知创建动作：%s" % action)
        if previous != self.editor.current:
            self._invalidate()
        return True

    def handle(self, action: str) -> bool:
        session = self.session
        if self._edit_action(action):
            return True
        stages = {
            "create_download": Page.CREATE_DOWNLOAD,
            "create_eula": Page.CREATE_EULA,
            "create_finish": Page.CREATE_FINISH,
        }
        prefix = action.split(".", 1)[0]
        if prefix in stages and session.page is not stages[prefix]:
            raise PmslError("操作不属于当前创建阶段。")
        if action == "create_download.tip":
            value = random.choice(self._tips) if self._tips else "当前没有提示语句。"
            lines = tuple(line[:120] for line in value.split("&")[:4])
            self._tip_lines = ("Tip:  " + lines[0],) + lines[1:]
            return True
        if action == "create_eula.eula-link":
            session.open_link("eula")
            return True
        if action == "create_download.download":
            if self.busy:
                return True
            if self.task is None:
                self.task = self._new_task()
            state = self.task.snapshot().state
            if state not in {
                CreationState.EDITING,
                CreationState.FAILED,
                CreationState.CANCELLED,
                CreationState.DOWNLOADED,
            }:
                raise PmslError("此任务已进入初始化或提交阶段，不能重新下载。")
            if state is not CreationState.DOWNLOADED:
                self.task.download()
            return True
        if action == "create_download.cancel":
            if self.task is not None:
                self.task.cancel()
            return True
        if action == "create_download.next":
            if (
                self.task is None
                or self.task.snapshot().state is not CreationState.DOWNLOADED
                or self.busy
            ):
                raise PmslError("核心尚未下载完成。")
            self.task.prepare(session._configured_java())
            session.select(Page.CREATE_EULA)
            return True
        if action == "create_download.back":
            if self.busy:
                raise PmslError("请先取消下载，等待连接关闭后再返回。")
            if self.task is not None and self.task.snapshot().state is CreationState.DOWNLOADED:
                if (
                    session.confirm(
                        text="【提示】 在核心下载完毕后返回上一个界面,需要重新下载核心",
                        title=session.title,
                        buttons=["返回", "取消"],
                    )
                    != "返回"
                ):
                    return True
            self._invalidate()
            session.select(Page.CREATE_SETTINGS)
            return True
        if action == "create_eula.refresh":
            if self.task is None:
                raise PmslError("尚无通过下载检查的创建任务。")
            state = self.task.snapshot().state
            if state in {CreationState.FAILED, CreationState.CANCELLED} and not self.busy:
                if (
                    session.confirm(
                        text="第一次运行服务器还未运行完毕!请等待运行结束后点击继续",
                        title=session.title,
                        buttons=["等待", "强制继续"],
                    )
                    == "强制继续"
                ):
                    # 保留按钮，但它只能重新安装/探测，不伪造 first_start=1。
                    self.task.prepare(session._configured_java())
            elif state in {CreationState.WAITING_FOR_EULA, CreationState.COMMITTING}:
                if not self._read_eula():
                    raise PmslError(self._eula_error or "EULA 文件为空，请重新初始化。")
            return True
        if action == "create_eula.accept":
            if self.task is None:
                raise PmslError("没有通过初始化校验的创建任务。")
            if self._eula_task != self.task.spec.task_id or not self._eula_lines:
                raise PmslError(self._eula_error or "尚未读取当前 EULA，请刷新后再确认。")
            self.task.accept_eula()
            session.select(Page.CREATE_FINISH)
            return True
        if action == "create_finish.finish":
            if self.task is None or not self.task.accepted or self.busy:
                raise PmslError("请先完成初始化并明确同意 EULA。")
            if self.task.snapshot().state is CreationState.COMPLETED:
                session.store.get(self.task.spec.task_id)
                session.select(Page.HOME)
                return True
            if any(
                name.casefold() == self.task.spec.name.casefold()
                for name in session._server_names()
            ):
                raise PmslError("目标服务器名称已经存在，未提交。")
            ServerOperations(session.storage).commit_creation(self.task.spec)
            self.task.mark_completed()
            session.home.preferred_id = self.task.spec.task_id
            session.select(Page.HOME)
            return True
        return False

    def update(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None or snapshot == self._observed:
            return
        if (
            snapshot.state is CreationState.DOWNLOADING
            and self._observed is not None
            and time.monotonic() - self._last_progress < 0.1
        ):
            return
        self._last_progress = time.monotonic()
        previous = self._observed
        self._observed = self._display = snapshot
        session = self.session
        # 只更新视图状态，最终结果不受下载进度限频影响。
        session.invalidate()
        if session.page is Page.CREATE_EULA and (
            previous is None or previous.state != snapshot.state
        ):
            if snapshot.state in {CreationState.WAITING_FOR_EULA, CreationState.COMMITTING}:
                if self._eula_task != snapshot.task_id or previous is not None:
                    self._read_eula()
                if self._eula_error and not session._exit_pending:
                    session.confirm(text=self._eula_error, title="ERROR", buttons=["继续"])
            elif (
                snapshot.state in {CreationState.FAILED, CreationState.CANCELLED}
                and not session._exit_pending
            ):
                session.confirm(
                    text=snapshot.error or "创建任务已取消。", title="ERROR", buttons=["继续"]
                )

    def close(self) -> None:
        if self.task is not None:
            self.task.close()
