from subprocess import Popen
from sys import platform as KPlatform
from types import FrameType

from KitCli.ForwardSignal import ForwardSignal


# one dispatcher keeps startup cancellation ordered across process creation and deferred job control
def RouteSignalMut(
    ChildProcesses: list[Popen[bytes]],
    PendingSignals: list[int],
    SignalNumber: int,
    Frame: FrameType | None,
) -> None:
    if KPlatform != "win32":
        from signal import SIGCONT, SIGTSTP

        if SignalNumber == SIGCONT:
            PendingSignals[:] = [
                Number for Number in PendingSignals if Number != SIGTSTP
            ]
    if ChildProcesses:
        ForwardSignal(ChildProcesses[0], SignalNumber, Frame)
        return
    PendingSignals.append(SignalNumber)
