"""定位 Java 可执行文件并探测运行时版本。"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pmsl.domain.errors import PmslError
from pmsl.infrastructure.paths import AppPaths


@dataclass(frozen=True)
class JavaInfo:
    executable: str
    major: int
    version: str
    output: str


class JavaDetector:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def detect(self, configured: Optional[str] = None) -> JavaInfo:
        executable = configured or shutil.which("java")
        if configured and Path(configured).is_dir():
            executable = str(Path(configured) / "bin" / ("java.exe" if os.name == "nt" else "java"))
        if not executable or not Path(executable).is_file():
            raise PmslError("未找到 Java，请在程序设置中选择有效的 Java 可执行文件或安装目录。")
        temporary = self.paths.data("tmp")
        temporary.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ, TEMP=str(temporary), TMP=str(temporary))
        try:
            result = subprocess.run(
                [str(Path(executable).resolve()), "-version"],
                cwd=str(self.paths.program_dir),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                check=False,
                creationflags=0x08000000 if os.name == "nt" else 0,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PmslError("Java 版本探测失败或超时。") from exc
        output = result.stdout.decode("utf-8", "replace")
        match = re.search(
            r'(?:openjdk|java)\s+(?:version\s+)?"?([0-9]+(?:[.0-9_+\-a-zA-Z]*))', output
        )
        if result.returncode != 0 or match is None:
            raise PmslError("Java 没有返回可识别的版本信息：%s" % output[:500])
        version = match.group(1)
        parts = version.split(".")
        major = int(parts[1]) if parts[0] == "1" and len(parts) > 1 else int(parts[0])
        return JavaInfo(str(Path(executable).resolve()), major, version, output)
