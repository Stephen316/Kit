import ctypes
from ctypes import wintypes

import pywintypes
import win32api
import win32con
import win32event

GET_PROCESS_TIMES = ctypes.WinDLL("kernel32", use_last_error=True).GetProcessTimes
FILETIME_POINTER = ctypes.POINTER(ctypes.c_ulonglong)
GET_PROCESS_TIMES.argtypes = [
    wintypes.HANDLE,
    FILETIME_POINTER,
    FILETIME_POINTER,
    FILETIME_POINTER,
    FILETIME_POINTER,
]
GET_PROCESS_TIMES.restype = wintypes.BOOL


def creation_time(handle):
    times = [ctypes.c_ulonglong() for _ in range(4)]
    if not GET_PROCESS_TIMES(handle, *[ctypes.byref(value) for value in times]):
        raise ctypes.WinError(ctypes.get_last_error())
    return f"windows:{times[0].value}"


def process_start(pid):
    try:
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_LIMITED_INFORMATION | win32con.SYNCHRONIZE,
            False,
            pid,
        )
    except pywintypes.error as error:
        if error.winerror == 87:
            return None
        raise OSError(
            f"process identity measurement failed: {error.winerror}"
        ) from error
    try:
        status = win32event.WaitForSingleObject(handle, 0)
        if status == win32event.WAIT_OBJECT_0:
            return None
        if status != win32event.WAIT_TIMEOUT:
            raise OSError("process identity wait failed")
        return creation_time(int(handle))
    finally:
        handle.Close()
