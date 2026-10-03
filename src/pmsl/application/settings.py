"""设置在写入成功后更新内存，绘制只读取当前快照。"""

from dataclasses import replace
from typing import Any

from pmsl.application.ports import SettingsStore
from pmsl.domain.models import AppSettings


class SettingsService:
    def __init__(self, store: SettingsStore) -> None:
        self.store = store
        self._current = store.load()

    @property
    def current(self) -> AppSettings:
        return self._current

    def update(self, **values: Any) -> AppSettings:
        candidate = replace(self._current, **values)
        self.store.save(candidate)
        self._current = candidate
        return candidate
