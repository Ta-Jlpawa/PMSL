"""入口分流和依赖组装，界面依赖按所选模式延迟加载。"""

import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional

from pmsl.domain.errors import PmslError
from pmsl.infrastructure.paths import AppPaths
from pmsl.infrastructure.storage import InstanceLock, JsonStorage


@contextmanager
def program_environment(paths: AppPaths) -> Iterator[None]:
    # 在入口统一管理程序工作目录和子进程临时目录。
    previous = Path.cwd()
    old_sys_path = list(sys.path)
    temporary = paths.data("tmp")
    temporary.mkdir(parents=True, exist_ok=True)
    old_temporary_environment = {key: os.environ.get(key) for key in ("TEMP", "TMP")}
    try:
        # 子进程继承程序内的临时目录。
        for key in ("TEMP", "TMP"):
            os.environ[key] = str(temporary)
        os.chdir(str(paths.program_dir))
        sys.path.insert(0, str(paths.program_dir))
        yield
    finally:
        sys.path[:] = old_sys_path
        os.chdir(str(previous))
        for key, value in old_temporary_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def launch_ui(paths: AppPaths, storage: JsonStorage, resume_task: Optional[str] = None) -> int:
    import pygame

    from pmsl.ui.app import App
    from pmsl.ui.assets import Assets
    from pmsl.ui.dialogs import Dialogs
    from pmsl.ui.layouts import WINDOW_SIZE
    from pmsl.ui.session import UiSession

    with program_environment(paths):
        pygame.init()
        assets = Assets(paths)
        dialogs = Dialogs()
        session = None
        app = None
        try:
            surface = pygame.display.set_mode(WINDOW_SIZE)
            pygame.display.set_caption("Py Minecraft Server 开服器", "By TA_JLPawa")
            pygame.display.set_icon(assets.load_image(paths.resource("imgs/icon.png"), alpha=False))
            pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])
            pygame.key.stop_text_input()
            pygame.key.set_repeat(500, 50)
            session = UiSession(paths, assets, dialogs, surface, storage=storage)
            if resume_task is not None:
                session.creation.resume(resume_task)
            app = App(surface, session)
            return app.run()
        finally:
            try:
                if app is not None:
                    app.close()
                if session is not None:
                    session.close()
                dialogs.close()
            finally:
                assets.clear()
                pygame.quit()


def main(arguments: Optional[List[str]] = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    parser = argparse.ArgumentParser(description="PMSL 服务器启动器")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--recover-operations", action="store_true", help="恢复创建或回收事务")
    mode.add_argument("--recover-settings", action="store_true", help="显式恢复新设置的有效备份")
    mode.add_argument(
        "--import-version-catalog", metavar="FILE", help="导入程序目录内的结构化离线版本目录"
    )
    mode.add_argument(
        "--import-download-sources", metavar="FILE", help="导入程序目录内的下载模板配置"
    )
    mode.add_argument("--list-trash", action="store_true", help="列出新版本服务器回收记录")
    mode.add_argument("--restore-server", metavar="TRASH_ID", help="从程序内回收区恢复服务器")
    mode.add_argument("--list-creations", action="store_true", help="列出未完成的新版本创建任务")
    mode.add_argument("--resume-creation", metavar="TASK_ID", help="在新界面继续指定创建任务")
    mode.add_argument("--paths", action="store_true", help="显示程序、资源和数据路径")
    mode.add_argument("--ui", action="store_true", help="启动重构界面（默认）")
    mode.add_argument("--runner", metavar="TASK_ID", help=argparse.SUPPRESS)
    mode.add_argument("--verify-installation", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument("--verify-window", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--task-token", help=argparse.SUPPRESS)
    parser.add_argument("--plan-hash", help=argparse.SUPPRESS)
    parser.add_argument("--program-dir", help=argparse.SUPPRESS)
    options = parser.parse_args(arguments)
    # 禁止 Python 在程序目录以外生成第三方库字节码。
    sys.dont_write_bytecode = True
    try:
        paths = AppPaths.discover()
        if options.runner:
            if not options.task_token or not options.plan_hash:
                raise PmslError("runner 缺少运行任务身份。")
            if options.program_dir:
                if getattr(sys, "frozen", False):
                    raise PmslError("冻结发行程序不能更改程序数据目录。")
                paths = AppPaths(Path(options.program_dir))
            from pmsl.infrastructure.runner import run_task

            return run_task(paths, options.runner, options.task_token, options.plan_hash)
        if options.program_dir or options.task_token or options.plan_hash:
            raise PmslError("运行任务参数只能用于 runner。")
        if options.verify_installation or options.verify_window:
            from pmsl.infrastructure.installation import verify_installation

            return verify_installation(paths, headless=not options.verify_window)
        if options.paths:
            print(
                json.dumps(
                    {
                        "program_dir": str(paths.program_dir),
                        "resources": str(paths.resource(".")),
                        "data_dir": str(paths.data_dir),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        with InstanceLock(paths) as lock:
            storage = JsonStorage(paths, lock)
            if options.import_version_catalog or options.import_download_sources:
                from pmsl.infrastructure.version_catalog import (
                    DownloadSourcesStore,
                    VersionCatalogStore,
                )

                if options.import_version_catalog:
                    VersionCatalogStore(storage).import_file(options.import_version_catalog)
                    print("已导入结构化离线版本目录。")
                else:
                    DownloadSourcesStore(storage).import_file(options.import_download_sources)
                    print("已导入下载来源配置。")
                return 0
            if options.recover_settings:
                from pmsl.infrastructure.catalog import JsonSettingsStore

                storage.recover_backup("settings.json", JsonSettingsStore(storage).validate)
                print("已恢复程序设置备份。")
                return 0
            from pmsl.application.operations import ServerOperations
            from pmsl.application.runtime import ServerRuntime

            ServerRuntime(paths).ensure_no_unconfirmed_tasks()
            operations = ServerOperations(storage)
            if options.recover_operations:
                count = operations.recover()
                print("已恢复 %d 个服务器事务。" % count)
                return 0
            if operations.pending():
                raise PmslError("存在未完成服务器事务，请先运行 --recover-operations。")
            if options.list_trash:
                print(json.dumps(operations.list_trash(), ensure_ascii=False, indent=2))
                return 0
            if options.restore_server:
                profile = operations.restore(options.restore_server)
                print("已恢复服务器：%s（%s）" % (profile.name, profile.id))
                return 0
            if options.list_creations:
                from pmsl.application.creation import CreationTask

                print(json.dumps(CreationTask.pending(storage), ensure_ascii=False, indent=2))
                return 0
            if options.resume_creation:
                return launch_ui(paths, storage, options.resume_creation)
            return launch_ui(paths, storage)
    except (PmslError, OSError) as exc:
        if sys.stderr is not None:
            print("PMSL：%s" % exc, file=sys.stderr)
        elif options.ui or options.resume_creation or not arguments:
            from pmsl.ui.dialogs import Dialogs

            dialogs = Dialogs()
            try:
                dialogs.confirm(text=str(exc), title="PMSL 无法启动", buttons=["返回"])
            finally:
                dialogs.close()
        return 1
