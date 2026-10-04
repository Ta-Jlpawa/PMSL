"""在程序目录内通过同目录暂存文件原子替换目标文件。"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Union

from pmsl.domain.errors import StorageError
from pmsl.infrastructure.paths import AppPaths


def atomic_write(paths: AppPaths, path: Union[str, Path], payload: bytes) -> None:
    target = paths.inside(path)
    temporary: Optional[Path] = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=str(target.parent),
            prefix=".%s-" % target.name,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        paths.inside(target)
        os.replace(str(temporary), str(target))
    except OSError as exc:
        raise StorageError("无法写入 %s：%s" % (target, exc)) from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
