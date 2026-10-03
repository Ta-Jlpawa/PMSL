"""创建任务的不可变输入、进度和启动配方。"""

from dataclasses import dataclass
from typing import Optional, Tuple

from pmsl.domain.models import CoreSelection
from pmsl.domain.states import CreationState


@dataclass(frozen=True)
class CreationSpec:
    task_id: str
    name: str
    selection: CoreSelection
    memory_gib: int


@dataclass(frozen=True)
class Artifact:
    url: str
    source: str
    sha256: Optional[str] = None


@dataclass(frozen=True)
class CreationSnapshot:
    task_id: str
    state: CreationState
    received: int = 0
    total: Optional[int] = None
    error: Optional[str] = None
    source: Optional[str] = None
    verified_upstream: bool = False


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int
    lines: Tuple[str, ...]
