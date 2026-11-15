import ctypes as CtypesApi
import sys as System
from ctypes import wintypes as WinTypes


def IsProcessAlive(ProcessId: int) -> bool:
    if System.platform != "win32":
        raise OSError("Windows liveness requires a Windows host")
    KernelApi = CtypesApi.WinDLL("kernel32", use_last_error=True)
    setattr(
        KernelApi.OpenProcess,
        "argtypes",
        [WinTypes.DWORD, WinTypes.BOOL, WinTypes.DWORD],
    )
    setattr(KernelApi.OpenProcess, "restype", WinTypes.HANDLE)
    setattr(
        KernelApi.WaitForSingleObject, "argtypes", [WinTypes.HANDLE, WinTypes.DWORD]
    )
    setattr(KernelApi.WaitForSingleObject, "restype", WinTypes.DWORD)
    setattr(KernelApi.CloseHandle, "argtypes", [WinTypes.HANDLE])
    setattr(KernelApi.CloseHandle, "restype", WinTypes.BOOL)
    HandleValue = KernelApi.OpenProcess(0x1000 | 0x100000, False, ProcessId)
    if not HandleValue:
        ErrorCode = CtypesApi.get_last_error()
        if ErrorCode == 87:
            return False
        raise OSError(ErrorCode, "process liveness query failed")
    try:
        WaitValue = KernelApi.WaitForSingleObject(HandleValue, 0)
        if WaitValue not in (0, 258):
            raise OSError(CtypesApi.get_last_error(), "process liveness wait failed")
        return WaitValue == 258
    finally:
        _ = KernelApi.CloseHandle(HandleValue)
