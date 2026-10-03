"""创建输入的关联选择；换游戏版本时清除不兼容的构建。"""

from dataclasses import replace

from pmsl.domain.errors import ValidationError
from pmsl.domain.models import CoreSelection
from pmsl.domain.validation import positive_integer, validate_legacy_name
from pmsl.domain.versions import CreationInput, VersionCatalog, validate_version


class CreationEditor:
    def __init__(self, catalog: VersionCatalog) -> None:
        self.catalog = catalog
        self.kind = "插件服"
        self.current = CreationInput("NewServer_1", catalog.select("Paper", "1.19.2"))

    def replace_input(self, value: CreationInput) -> None:
        validate_legacy_name(value.name)
        positive_integer(value.memory_gib, "运行内存")
        if value.selection.core not in {"Paper", "Spigot", "Fabric", "Forge"}:
            raise ValidationError("不支持的服务器核心。")
        for token in (
            value.selection.minecraft_version,
            value.selection.build,
            value.selection.loader,
            value.selection.installer,
        ):
            if token is not None:
                validate_version(token)
        self.current = value

    def set_kind(self, kind: str) -> None:
        if kind not in {"插件服", "模组服"}:
            raise ValidationError("不支持的服务器类型。")
        core = self.current.selection.core
        allowed = ("Spigot", "Paper") if kind == "插件服" else ("Fabric", "Forge")
        if core not in allowed:
            self.choose_core(allowed[0])
        self.kind = kind

    def choose_core(self, core: str) -> None:
        selection = self.catalog.select(core, self.current.selection.minecraft_version)
        self.current = replace(self.current, selection=selection)

    def choose_game(self, version: str) -> None:
        previous = self.current.selection
        self.catalog.release(previous.core, version)
        if previous.core == "Fabric":
            selection = replace(previous, minecraft_version=version)
        else:
            selection = self.catalog.select(previous.core, version)
            if previous.build in {
                build.version for build in self.catalog.release(previous.core, version).builds
            }:
                selection = replace(selection, build=previous.build)
        self.current = replace(self.current, selection=selection)

    def choose_component(self, component: str, version: str) -> None:
        selection = self.current.selection
        if component not in {"build", "loader", "installer"}:
            raise ValidationError("未知核心版本字段。")
        candidate = replace(selection, **{component: version})
        self.catalog.validate_selection(candidate)
        self.current = replace(self.current, selection=candidate)

    def name(self, value: str) -> None:
        validate_legacy_name(value)
        if len(value) > 12:
            raise ValidationError("服务器名称必须大于0个字符并且小于等于12个字符。")
        self.current = replace(self.current, name=value)

    def memory(self, value: int) -> None:
        self.current = replace(self.current, memory_gib=positive_integer(value, "运行内存"))

    def validate(self) -> CoreSelection:
        self.catalog.validate_selection(self.current.selection)
        return self.current.selection
