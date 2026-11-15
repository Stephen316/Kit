import sys as System


def IsProcessAlive(ProcessId: int) -> bool:
    if System.platform != "win32":
        raise OSError("Windows liveness requires a Windows host")
    import pywintypes as WinErrors
    import win32api as WinApi
    import win32con as WinCodes
    import win32event as WinEvents

    try:
        HandleValue = WinApi.OpenProcess(
            WinCodes.PROCESS_QUERY_LIMITED_INFORMATION | WinCodes.SYNCHRONIZE,
            False,
            ProcessId,
        )
    except WinErrors.error as Failure:
        if Failure.winerror == 87:
            return False
        raise OSError(Failure.winerror, "process liveness query failed") from Failure
    try:
        WaitValue = WinEvents.WaitForSingleObject(HandleValue, 0)
        if WaitValue not in (WinEvents.WAIT_OBJECT_0, WinEvents.WAIT_TIMEOUT):
            raise OSError("process liveness wait failed")
        return WaitValue == WinEvents.WAIT_TIMEOUT
    finally:
        WinApi.CloseHandle(HandleValue)
