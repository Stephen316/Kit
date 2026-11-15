from signal import SIG_DFL, raise_signal as RaiseSignal, signal as SetSignal
from sys import platform as KPlatform
from typing import NoReturn


# callers must observe the same failure status or terminating signal as the research tool
def ExitResearch(ReturnCode: int) -> NoReturn:
    if KPlatform != "win32" and ReturnCode < 0:
        from signal import SIGKILL, SIGSTOP

        SignalNumber = -ReturnCode
        if SignalNumber not in (SIGKILL, SIGSTOP):
            _ = SetSignal(SignalNumber, SIG_DFL)
        RaiseSignal(SignalNumber)
    raise SystemExit(ReturnCode)
