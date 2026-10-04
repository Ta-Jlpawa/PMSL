"""封装 Windows 目录权限、进程身份查询、控制台和进程树管理。"""

import ctypes
import os
import sys
from ctypes import wintypes as w
from typing import Any, Dict

from pmsl.domain.errors import PmslError


def _kernel() -> Any:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    return kernel


def protect_directory(path: str) -> None:
    if os.name != "nt":
        os.chmod(path, 0o700)
        return
    kernel = _kernel()
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    security.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
    security.GetTokenInformation.argtypes = [
        w.HANDLE,
        ctypes.c_int,
        w.LPVOID,
        w.DWORD,
        ctypes.POINTER(w.DWORD),
    ]
    security.ConvertSidToStringSidW.argtypes = [w.LPVOID, ctypes.POINTER(w.LPWSTR)]
    security.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        w.LPCWSTR,
        w.DWORD,
        ctypes.POINTER(w.LPVOID),
        ctypes.POINTER(w.DWORD),
    ]
    security.SetFileSecurityW.argtypes = [w.LPCWSTR, w.DWORD, w.LPVOID]
    kernel.LocalFree.argtypes = [w.LPVOID]
    kernel.LocalFree.restype = w.LPVOID
    token = w.HANDLE()
    sid_text = w.LPWSTR()
    descriptor = w.LPVOID()
    try:
        if not security.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
            raise ctypes.WinError(ctypes.get_last_error())
        size = w.DWORD()
        security.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        buffer = ctypes.create_string_buffer(size.value)
        if not security.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        sid = ctypes.cast(buffer, ctypes.POINTER(w.LPVOID))[0]
        if not security.ConvertSidToStringSidW(sid, ctypes.byref(sid_text)):
            raise ctypes.WinError(ctypes.get_last_error())
        # 限定当前用户和 SYSTEM 可访问目录，并让子文件继承此权限。
        sddl = "D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;%s)" % sid_text.value
        if not security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(descriptor), None
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if not security.SetFileSecurityW(path, 4 | 0x80000000, descriptor):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        if descriptor:
            kernel.LocalFree(descriptor)
        if sid_text:
            kernel.LocalFree(ctypes.cast(sid_text, w.LPVOID))
        if token:
            kernel.CloseHandle(token)


def process_identity(pid: int) -> Dict[str, object]:
    if os.name != "nt":
        # 非 Windows 平台仅返回 PID，创建时间和执行路径留空。
        return {"pid": pid, "created": None, "executable": None}
    kernel = _kernel()
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [
        w.HANDLE,
        w.DWORD,
        w.LPWSTR,
        ctypes.POINTER(w.DWORD),
    ]
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    handle = kernel.OpenProcess(0x1000 | 0x100000, False, pid)
    if not handle:
        raise PmslError("无法确认运行任务的进程身份。")
    try:
        if kernel.WaitForSingleObject(handle, 0) == 0:
            raise PmslError("运行任务的进程已经退出。")
        times = [w.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        length = w.DWORD(32768)
        executable = ctypes.create_unicode_buffer(length.value)
        if not kernel.QueryFullProcessImageNameW(handle, 0, executable, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        return {
            "pid": pid,
            "created": str(times[0].dwHighDateTime << 32 | times[0].dwLowDateTime),
            "executable": executable.value,
        }
    except OSError as exc:
        raise PmslError("无法确认运行任务的进程身份。") from exc
    finally:
        kernel.CloseHandle(handle)


def open_console() -> None:
    if os.name != "nt":
        return
    kernel = _kernel()
    kernel.GetConsoleWindow.restype = w.HWND
    if not kernel.GetConsoleWindow() and not kernel.AllocConsole():
        raise ctypes.WinError(ctypes.get_last_error())
    kernel.SetConsoleCP(65001)
    kernel.SetConsoleOutputCP(65001)
    sys.stdin = open("CONIN$", "r", encoding="utf-8")
    sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
    sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", w.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", w.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", w.DWORD),
        ("SchedulingClass", w.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in (
            "ReadOperationCount",
            "WriteOperationCount",
            "OtherOperationCount",
            "ReadTransferCount",
            "WriteTransferCount",
            "OtherTransferCount",
        )
    ]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimits),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _ThreadEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", w.DWORD),
        ("cntUsage", w.DWORD),
        ("th32ThreadID", w.DWORD),
        ("th32OwnerProcessID", w.DWORD),
        ("tpBasePri", w.LONG),
        ("tpDeltaPri", w.LONG),
        ("dwFlags", w.DWORD),
    ]


class ProcessTree:
    def __init__(self) -> None:
        self.handle: Any = None
        self.kernel: Any = None
        if os.name != "nt":
            return
        self.kernel = kernel = _kernel()
        kernel.CreateJobObjectW.argtypes = [w.LPVOID, w.LPCWSTR]
        kernel.CreateJobObjectW.restype = w.HANDLE
        kernel.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD]
        kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        kernel.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
        self.handle = kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        if not kernel.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def attach_and_resume(self, process: Any) -> None:
        if os.name != "nt":
            return
        kernel = self.kernel
        if not kernel.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
        kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
        kernel.Thread32First.argtypes = [w.HANDLE, ctypes.POINTER(_ThreadEntry)]
        kernel.Thread32Next.argtypes = [w.HANDLE, ctypes.POINTER(_ThreadEntry)]
        kernel.OpenThread.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        kernel.OpenThread.restype = w.HANDLE
        kernel.ResumeThread.argtypes = [w.HANDLE]
        kernel.ResumeThread.restype = w.DWORD
        snapshot = kernel.CreateToolhelp32Snapshot(4, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        resumed = False
        try:
            entry = _ThreadEntry()
            entry.dwSize = ctypes.sizeof(entry)
            found = kernel.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.th32OwnerProcessID == process.pid:
                    thread = kernel.OpenThread(2, False, entry.th32ThreadID)
                    if not thread:
                        raise ctypes.WinError(ctypes.get_last_error())
                    try:
                        if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                            raise ctypes.WinError(ctypes.get_last_error())
                        resumed = True
                    finally:
                        kernel.CloseHandle(thread)
                    break
                found = kernel.Thread32Next(snapshot, ctypes.byref(entry))
        finally:
            kernel.CloseHandle(snapshot)
        if not resumed:
            raise PmslError("无法恢复已登记到任务的子进程。")

    def close(self) -> None:
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
