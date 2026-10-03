"""运行状态和有界日志快照。"""

from dataclasses import dataclass
from typing import Optional, Tuple

from pmsl.domain.states import ProcessState


@dataclass(frozen=True)
class RuntimeSnapshot:
    task_id: str
    server_id: str
    state: ProcessState
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    ready: bool = False
    stop_timed_out: bool = False
    error: Optional[str] = None

    @property
    def active(self) -> bool:
        return self.state in {ProcessState.STARTING, ProcessState.RUNNING, ProcessState.STOPPING}


@dataclass(frozen=True)
class LogSnapshot:
    revision: int
    lines: Tuple[str, ...]
