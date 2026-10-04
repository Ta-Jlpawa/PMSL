"""读取服务器属性，检查外部修改冲突并保存单项属性变更。"""

from typing import Optional

from pmsl.domain.errors import StorageError, ValidationError
from pmsl.domain.models import ServerProfile
from pmsl.domain.server_properties import EDITABLE_KEYS, PropertiesSnapshot
from pmsl.infrastructure.catalog import JsonServerStore
from pmsl.infrastructure.properties import PropertiesDocument, validate_property
from pmsl.infrastructure.server_layout import ServerLayout
from pmsl.infrastructure.storage import JsonStorage


class ServerPropertyStore:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage, self.paths = storage, storage.paths
        self.servers = JsonServerStore(storage)
        self.layout = ServerLayout(self.paths)

    def _snapshot(
        self, profile: ServerProfile, document: Optional[PropertiesDocument]
    ) -> PropertiesSnapshot:
        return PropertiesSnapshot(
            profile.id,
            profile.name,
            tuple(
                (key, document.get(key) if document is not None else None) for key in EDITABLE_KEYS
            ),
            document is not None,
        )

    def load(self, server_id: str) -> PropertiesSnapshot:
        profile = self.servers.get(server_id)
        path = self.layout.file(profile, "server.properties")
        try:
            document = PropertiesDocument.read(self.paths, path)
        except FileNotFoundError:
            document = None
        return self._snapshot(profile, document)

    def update(
        self, server_id: str, key: str, value: str, expected: Optional[str]
    ) -> PropertiesSnapshot:
        self.storage._require_lock()
        if key not in EDITABLE_KEYS or not isinstance(value, str) or "\0" in value:
            raise ValidationError("不支持的属性或属性值无效。")
        validate_property(key, value)
        profile = self.servers.get(server_id)
        path = self.layout.file(profile, "server.properties")
        try:
            document = PropertiesDocument.read(self.paths, path)
        except FileNotFoundError as exc:
            raise StorageError("服务器属性文件缺失，未创建替代文件。") from exc
        before = document.to_bytes()
        current = document.get(key)
        if current is None or expected is None:
            raise ValidationError("当前服务器未提供属性：%s，未写入。" % key)
        if current != expected:
            raise StorageError("该属性已被外部修改，请重新进入页面刷新后再编辑。")
        document.set(key, value)
        # 写入前再次校验目录身份和文件内容，检测读取后的外部修改。
        self.layout.file(self.servers.get(server_id), "server.properties")
        if path.read_bytes() != before:
            raise StorageError("保存前属性文件发生变化，请刷新后重试。")
        document.save(self.paths, path)
        return self._snapshot(profile, document)
