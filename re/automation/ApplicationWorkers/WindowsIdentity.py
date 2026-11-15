import ctypes
from ctypes import wintypes

KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
ERROR_INVALID_PARAMETER = 87
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258

OPEN_PROCESS = KERNEL.OpenProcess
OPEN_PROCESS.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OPEN_PROCESS.restype = wintypes.HANDLE
WAIT_FOR_OBJECT = KERNEL.WaitForSingleObject
WAIT_FOR_OBJECT.argtypes = [wintypes.HANDLE, wintypes.DWORD]
WAIT_FOR_OBJECT.restype = wintypes.DWORD
CLOSE_HANDLE = KERNEL.CloseHandle
CLOSE_HANDLE.argtypes = [wintypes.HANDLE]
CLOSE_HANDLE.restype = wintypes.BOOL

GET_PROCESS_TIMES = KERNEL.GetProcessTimes
FILETIME_POINTER = ctypes.POINTER(wintypes.FILETIME)
GET_PROCESS_TIMES.argtypes = [
    wintypes.HANDLE,
    FILETIME_POINTER,
    FILETIME_POINTER,
    FILETIME_POINTER,
    FILETIME_POINTER,
]
GET_PROCESS_TIMES.restype = wintypes.BOOL


def creation_time(handle):
    times = [wintypes.FILETIME() for _ in range(4)]
    if not GET_PROCESS_TIMES(handle, *[ctypes.byref(value) for value in times]):
        raise ctypes.WinError(ctypes.get_last_error())
    created = times[0]
    return f"windows:{(created.dwHighDateTime << 32) | created.dwLowDateTime}"


def process_start(pid):
    # ctypes narrows a DWORD argument, so guard against aliasing another PID.
    if not 0 <= pid <= 0xFFFFFFFF:
        raise OverflowError("Windows process identifier is outside the DWORD range")
    handle = OPEN_PROCESS(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == ERROR_INVALID_PARAMETER:
            return None
        raise OSError(f"process identity measurement failed: {error}")
    try:
        status = WAIT_FOR_OBJECT(handle, 0)
        if status == WAIT_OBJECT_0:
            return None
        if status != WAIT_TIMEOUT:
            raise OSError("process identity wait failed")
        return creation_time(handle)
    finally:
        if not CLOSE_HANDLE(handle):
            raise ctypes.WinError(ctypes.get_last_error())
