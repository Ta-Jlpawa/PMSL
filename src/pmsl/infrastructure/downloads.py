"""下载核心和版本元数据，处理重试、取消、缓存及文件校验。"""

import hashlib
import http.client
import json
import os
import re
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

from pmsl.domain.creation import Artifact
from pmsl.domain.errors import DownloadError, TaskCancelled
from pmsl.infrastructure.files import atomic_write
from pmsl.infrastructure.paths import AppPaths

USER_AGENT = "PMSL/1.2.0 (https://github.com/Ta-Jlpawa/PMSL)"
MAX_DOWNLOAD = 1024 * 1024 * 1024


def check_cancel(cancel: threading.Event) -> None:
    if cancel.is_set():
        raise TaskCancelled("创建任务已取消。")


def validate_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise DownloadError("下载地址必须为不含登录信息的 HTTP(S) 地址。")
    if any(character in url for character in "\r\n\x00"):
        raise DownloadError("下载地址含有无效字符。")
    return url


def validate_jar(path: Path, cancel: threading.Event) -> Optional[int]:
    try:
        with zipfile.ZipFile(path) as jar:
            entries = jar.infolist()
            if len(entries) > 100000 or sum(item.file_size for item in entries) > 2 * MAX_DOWNLOAD:
                raise DownloadError("JAR 解压内容超过校验限制。")
            if "META-INF/MANIFEST.MF" not in jar.namelist():
                raise DownloadError("下载内容缺少 JAR 清单，不能作为服务器核心。")
            main_class = None
            for item in entries:
                check_cancel(cancel)
                if (
                    item.file_size > MAX_DOWNLOAD
                    or item.file_size > max(1, item.compress_size) * 1000
                ):
                    raise DownloadError("JAR 条目超过校验限制。")
                with jar.open(item) as stream:
                    while stream.read(65536):
                        check_cancel(cancel)
            manifest_info = jar.getinfo("META-INF/MANIFEST.MF")
            if manifest_info.file_size > 1024 * 1024:
                raise DownloadError("JAR 清单过大。")
            manifest = (
                jar.read(manifest_info)
                .decode("utf-8", "replace")
                .replace("\r\n ", "")
                .replace("\n ", "")
            )
            match = re.search(r"^Main-Class:\s*(\S+)\s*$", manifest, re.MULTILINE)
            if match:
                main_class = match.group(1).replace(".", "/") + ".class"
            if main_class is None:
                raise DownloadError("下载的 JAR 没有可执行入口。")
            if main_class in jar.namelist():
                with jar.open(main_class) as stream:
                    header = stream.read(8)
                if len(header) == 8 and header[:4] == b"\xca\xfe\xba\xbe":
                    return max(1, int.from_bytes(header[6:8], "big") - 44)
            return None
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise DownloadError("下载内容不是完整有效的 JAR。") from exc


class HttpClient:
    def open(self, url: str) -> Any:
        request = urllib.request.Request(
            validate_url(url), headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
        )
        return urllib.request.urlopen(request, timeout=10)


class MetadataClient:
    def __init__(self, paths: AppPaths, http: Optional[HttpClient] = None) -> None:
        self.paths = paths
        self.http = http if http is not None else HttpClient()

    def get(self, url: str, cancel: threading.Event) -> Any:
        check_cancel(cancel)
        key = hashlib.sha256(validate_url(url).encode()).hexdigest()
        target = self.paths.data("cache/catalogs/" + key + ".json")
        try:
            with self.http.open(url) as response:
                validate_url(response.geturl())
                blocks = bytearray()
                read = getattr(response, "read1", response.read)
                while True:
                    check_cancel(cancel)
                    block = read(65536)
                    if not block:
                        break
                    blocks.extend(block)
                    if len(blocks) > 8 * 1024 * 1024:
                        raise DownloadError("核心目录响应超过大小限制。")
                payload = bytes(blocks)
            check_cancel(cancel)
            if len(payload) > 8 * 1024 * 1024:
                raise DownloadError("核心目录响应超过大小限制。")
            result = json.loads(payload.decode("utf-8"))
        except (OSError, ValueError, urllib.error.URLError, http.client.HTTPException) as exc:
            check_cancel(cancel)
            if target.is_file():
                try:
                    cached = json.loads(target.read_text(encoding="utf-8"))
                    if cached.get("schema_version") == 1 and cached.get("url") == url:
                        return cached["data"]
                except (OSError, ValueError, KeyError, AttributeError):
                    pass
            raise DownloadError("无法获取所选核心的目录，也没有可用的同地址缓存。") from exc
        document = dict(schema_version=1, url=url, data=result)
        atomic_write(self.paths, target, json.dumps(document, ensure_ascii=False).encode("utf-8"))
        return result


class Downloader:
    def __init__(self, paths: AppPaths, http: Optional[HttpClient] = None) -> None:
        self.paths = paths
        self.http = http if http is not None else HttpClient()

    def fetch(
        self,
        artifact: Artifact,
        cancel: threading.Event,
        progress: Callable[[int, Optional[int]], None],
    ) -> Path:
        validate_url(artifact.url)
        if (
            artifact.sha256 is not None
            and re.fullmatch(r"[0-9a-fA-F]{64}", artifact.sha256) is None
        ):
            raise DownloadError("上游 SHA-256 摘要格式无效。")
        key = hashlib.sha256((artifact.url + ":" + (artifact.sha256 or "")).encode()).hexdigest()
        target = self.paths.data("cache/downloads/" + key + ".jar")
        receipt = self.paths.data("cache/downloads/" + key + ".json")
        if target.is_file() and receipt.is_file():
            try:
                document = json.loads(receipt.read_text(encoding="utf-8"))
                digest = self._digest(target, cancel)
                if (
                    document.get("url") == artifact.url
                    and document.get("sha256") == digest
                    and (artifact.sha256 is None or artifact.sha256.lower() == digest)
                ):
                    validate_jar(target, cancel)
                    progress(target.stat().st_size, target.stat().st_size)
                    return target
            except (OSError, ValueError, DownloadError):
                pass
        target.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(3):
            check_cancel(cancel)
            partial = self.paths.inside(target.parent / ("." + key + "-" + uuid4().hex + ".part"))
            try:
                with self.http.open(artifact.url) as response, partial.open("xb") as output:
                    validate_url(response.geturl())
                    if "text/html" in response.headers.get("Content-Type", "").lower():
                        raise DownloadError("下载返回了 HTML 页面，未保存为核心。")
                    header = response.headers.get("Content-Length")
                    total = (
                        int(header) if header and header.isdecimal() and int(header) > 0 else None
                    )
                    if total is not None and total > MAX_DOWNLOAD:
                        raise DownloadError("下载文件超过大小限制。")
                    received = 0
                    progress(received, total)
                    read = getattr(response, "read1", response.read)
                    while True:
                        check_cancel(cancel)
                        block = read(65536)
                        if not block:
                            break
                        received += len(block)
                        if received > MAX_DOWNLOAD:
                            raise DownloadError("下载文件超过大小限制。")
                        output.write(block)
                        progress(received, total)
                    output.flush()
                    os.fsync(output.fileno())
                check_cancel(cancel)
                if total is not None and received != total:
                    raise DownloadError("核心下载长度不符，文件未提交。")
                digest = self._digest(partial, cancel)
                if artifact.sha256 is not None and digest != artifact.sha256.lower():
                    raise DownloadError("核心摘要与上游不符，文件未提交。")
                validate_jar(partial, cancel)
                check_cancel(cancel)
                os.replace(str(partial), str(self.paths.inside(target)))
                document = dict(
                    schema_version=1,
                    url=artifact.url,
                    source=artifact.source,
                    sha256=digest,
                    upstream_sha256=artifact.sha256,
                )
                atomic_write(self.paths, receipt, json.dumps(document).encode())
                return target
            except urllib.error.HTTPError as exc:
                if exc.code not in {408, 429, 500, 502, 503, 504} or attempt == 2:
                    raise DownloadError("核心下载 HTTP 错误：%d" % exc.code) from exc
            except (
                urllib.error.URLError,
                socket.timeout,
                ConnectionError,
                http.client.HTTPException,
            ) as exc:
                if attempt == 2:
                    raise DownloadError("核心下载连接失败或超时。") from exc
            finally:
                if partial.exists():
                    partial.unlink()
            if cancel.wait(0.2 * (attempt + 1)):
                check_cancel(cancel)
        raise DownloadError("核心下载失败。")

    @staticmethod
    def _digest(path: Path, cancel: threading.Event) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                check_cancel(cancel)
                block = stream.read(65536)
                if not block:
                    return digest.hexdigest()
                digest.update(block)
