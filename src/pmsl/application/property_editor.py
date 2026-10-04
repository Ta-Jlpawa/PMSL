"""管理服务器属性的读取和修改，保存当前编辑快照。"""

from typing import Optional, Protocol

from pmsl.domain.errors import ValidationError
from pmsl.domain.server_properties import PropertiesSnapshot


class PropertyStore(Protocol):
    def load(self, server_id: str) -> PropertiesSnapshot: ...

    def update(
        self, server_id: str, key: str, value: str, expected: Optional[str]
    ) -> PropertiesSnapshot: ...


class PropertyEditor:
    def __init__(self, store: PropertyStore) -> None:
        self.store = store
        self.current: Optional[PropertiesSnapshot] = None

    def load(self, server_id: str) -> PropertiesSnapshot:
        snapshot = self.store.load(server_id)
        self.current = snapshot
        return snapshot

    def change(self, key: str, value: str) -> PropertiesSnapshot:
        if self.current is None:
            raise ValidationError("请先选择服务器。")
        snapshot = self.store.update(self.current.server_id, key, value, self.current.get(key))
        self.current = snapshot
        return snapshot
