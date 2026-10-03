"""四类核心的确切版本解析与安全下载模板。"""

import re
import string
import threading
from typing import Dict, Optional
from urllib.parse import quote

from pmsl.domain.creation import Artifact
from pmsl.domain.errors import DownloadError
from pmsl.domain.models import CoreSelection
from pmsl.infrastructure.downloads import MetadataClient, validate_url


def version_token(value: Optional[str], label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-zA-Z][0-9a-zA-Z._+\-]*", value):
        raise DownloadError("%s 未选择有效版本。" % label)
    return value


def validate_template(core: str, template: str) -> None:
    allowed = {
        "Spigot": {"mc_version"},
        "Paper": {"mc_version", "core_version", "paper_code"},
        "Forge": {"mc_version", "core_version"},
        "Fabric": {"mc_version", "core_version_L", "core_version_I"},
    }
    if core not in allowed or not isinstance(template, str) or not template:
        raise DownloadError("下载模板的核心或地址无效。")
    try:
        for _, key, spec, conversion in string.Formatter().parse(template):
            if key is not None and (key not in allowed[core] or spec or conversion):
                raise DownloadError("下载模板包含未知占位符或格式表达式。")
        validate_url(template.format_map({key: "1" for key in allowed[core]}))
    except ValueError as exc:
        raise DownloadError("下载模板格式错误。") from exc


class CoreProviders:
    def __init__(
        self,
        metadata: MetadataClient,
        templates: Optional[Dict[str, str]] = None,
        paper_codes: Optional[Dict[str, str]] = None,
    ) -> None:
        self.metadata = metadata
        self.templates = dict(templates or {})
        self.paper_codes = dict(paper_codes or {})

    def resolve(self, selection: CoreSelection, cancel: threading.Event) -> Artifact:
        mc = version_token(selection.minecraft_version, "Minecraft")
        core = selection.core
        if core not in {"Paper", "Spigot", "Fabric", "Forge"}:
            raise DownloadError("不支持的核心：%s" % core)
        build = version_token(selection.build, "核心") if core in {"Paper", "Forge"} else None
        loader = version_token(selection.loader, "Fabric Loader") if core == "Fabric" else None
        installer = (
            version_token(selection.installer, "Fabric Installer") if core == "Fabric" else None
        )
        if core in self.templates:
            fields = dict(
                mc_version=mc,
                core_version=build or "",
                core_version_L=loader or "",
                core_version_I=installer or "",
                paper_code=self.paper_codes.get(
                    mc + ":" + str(build), self.paper_codes.get(mc, "")
                ),
            )
            template = self.templates[core]
            validate_template(core, template)
            try:
                for _, key, spec, conversion in string.Formatter().parse(template):
                    if key is not None and (
                        key not in fields or spec or conversion or not fields[key]
                    ):
                        raise DownloadError("自定义下载模板包含未知或未选择的占位符。")
                url = template.format_map(fields)
            except ValueError as exc:
                raise DownloadError("自定义下载模板格式错误。") from exc
            return Artifact(validate_url(url), "自定义下载模板（无上游摘要）")
        if core == "Paper":
            url = "https://fill.papermc.io/v3/projects/paper/versions/%s/builds" % quote(
                mc, safe=""
            )
            builds = self.metadata.get(url, cancel)
            if not isinstance(builds, list):
                raise DownloadError("Paper 返回了无效构建目录。")
            selected = next(
                (
                    item
                    for item in builds
                    if isinstance(item, dict) and str(item.get("id")) == build
                ),
                None,
            )
            if selected is None:
                raise DownloadError("Paper 目录中没有所选构建，未自动更换版本。")
            try:
                download = selected["downloads"]["server:default"]
                return Artifact(
                    validate_url(download["url"]),
                    "PaperMC Fill v3",
                    download.get("checksums", {}).get("sha256"),
                )
            except (KeyError, TypeError, AttributeError) as exc:
                raise DownloadError("Paper 所选构建没有可用的服务器下载。") from exc
        if core == "Fabric":
            url = "https://meta.fabricmc.net/v2/versions/loader/%s/%s/%s/server/jar" % (
                mc,
                loader,
                installer,
            )
            return Artifact(url, "Fabric Meta（无上游摘要）")
        if core == "Forge":
            coordinate = mc + "-" + str(build)
            return Artifact(
                "https://maven.minecraftforge.net/net/minecraftforge/forge/%s/forge-%s-installer.jar"
                % (coordinate, coordinate),
                "Forge Maven（无上游摘要）",
            )
        return Artifact(
            "https://cdn.getbukkit.org/spigot/spigot-%s.jar" % mc,
            "GetBukkit 第三方 Spigot 来源（无上游摘要）",
        )
