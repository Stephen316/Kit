import ctypes
import msvcrt
import os
import shutil
import subprocess
from ctypes import wintypes

from ApplicationWorkers.WindowsIdentity import creation_time


KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)
POINTER = ctypes.c_void_p
SIZE = ctypes.c_size_t


class StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR), ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR), ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD), ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD), ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD), ("lpReserved2", POINTER),
        ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE),
    ]


class StartupInfoEx(ctypes.Structure):
    _fields_ = [("StartupInfo", StartupInfo), ("lpAttributeList", POINTER)]


class ProcessInfo(ctypes.Structure):
    _fields_ = [("process", wintypes.HANDLE), ("thread", wintypes.HANDLE), ("pid", wintypes.DWORD), ("tid", wintypes.DWORD)]


KERNEL.InitializeProcThreadAttributeList.argtypes = [POINTER, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(SIZE)]
KERNEL.InitializeProcThreadAttributeList.restype = wintypes.BOOL
KERNEL.UpdateProcThreadAttribute.argtypes = [POINTER, wintypes.DWORD, SIZE, POINTER, SIZE, POINTER, POINTER]
KERNEL.UpdateProcThreadAttribute.restype = wintypes.BOOL
KERNEL.DeleteProcThreadAttributeList.argtypes = [POINTER]
KERNEL.DeleteProcThreadAttributeList.restype = None
KERNEL.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, POINTER, POINTER, wintypes.BOOL, wintypes.DWORD, POINTER, wintypes.LPCWSTR, POINTER, ctypes.POINTER(ProcessInfo)]
KERNEL.CreateProcessW.restype = wintypes.BOOL
KERNEL.CloseHandle.argtypes = [wintypes.HANDLE]
KERNEL.CloseHandle.restype = wintypes.BOOL


def require_success(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def create_suspended(argv, root, environment, stdout, stderr, job):
    executable = shutil.which(argv[0], path=environment.get("PATH"))
    if executable is None:
        raise FileNotFoundError(f"runner executable is unavailable: {argv[0]}")
    info = ProcessInfo()
    startup = StartupInfoEx()
    startup.StartupInfo.cb = ctypes.sizeof(startup)
    startup.StartupInfo.dwFlags = 0x100
    attribute_size = SIZE()
    KERNEL.InitializeProcThreadAttributeList(None, 2, 0, ctypes.byref(attribute_size))
    if ctypes.get_last_error() != 122 or not attribute_size.value:
        raise ctypes.WinError(ctypes.get_last_error())
    attributes = ctypes.create_string_buffer(attribute_size.value)
    require_success(KERNEL.InitializeProcThreadAttributeList(attributes, 2, 0, ctypes.byref(attribute_size)))
    startup.lpAttributeList = ctypes.cast(attributes, POINTER)
    source = os.open(os.devnull, os.O_RDONLY)
    handles = [msvcrt.get_osfhandle(source), msvcrt.get_osfhandle(stdout), msvcrt.get_osfhandle(stderr)]
    previous = [os.get_handle_inheritable(handle) for handle in handles]
    try:
        for handle in handles:
            os.set_handle_inheritable(handle, True)
        startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = handles
        inherited = (wintypes.HANDLE * len(handles))(*handles)
        require_success(KERNEL.UpdateProcThreadAttribute(startup.lpAttributeList, 0, 0x20002, inherited, ctypes.sizeof(inherited), None, None))
        jobs = (wintypes.HANDLE * 1)(job)
        require_success(KERNEL.UpdateProcThreadAttribute(startup.lpAttributeList, 0, 0x2000D, jobs, ctypes.sizeof(jobs), None, None))
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        env = ctypes.create_unicode_buffer("\0".join(f"{key}={value}" for key, value in sorted(environment.items(), key=lambda item: item[0].upper())) + "\0\0")
        require_success(KERNEL.CreateProcessW(executable, command, None, None, True, 0x4 | 0x200 | 0x400 | 0x80000, env, str(root), ctypes.byref(startup), ctypes.byref(info)))
        return info
    finally:
        for handle, inheritable in zip(handles, previous, strict=True):
            os.set_handle_inheritable(handle, inheritable)
        os.close(source)
        KERNEL.DeleteProcThreadAttributeList(startup.lpAttributeList)
