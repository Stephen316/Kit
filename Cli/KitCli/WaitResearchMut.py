from subprocess import Popen

from KitCli.ForwardSignal import ForwardSignal


# waiting must preserve research cleanup while the launcher owns terminal signal delivery
def WaitResearchMut(
    ChildProcess: Popen[bytes],
    PendingSignals: list[int],
) -> int:
    while PendingSignals:
        ForwardSignal(ChildProcess, PendingSignals.pop(0), None)
    while True:
        try:
            return ChildProcess.wait()
        except KeyboardInterrupt:
            continue
