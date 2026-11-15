import time as TimeClock

from tests.Research.Windows.IsProcessAlive import IsProcessAlive


# termination checks must allow asynchronous kernel cleanup before declaring that a process escaped
def WaitForExit(ProcessId: int, Timeout: float = 15) -> None:
    UntilTime = TimeClock.monotonic() + Timeout
    while IsProcessAlive(ProcessId) and TimeClock.monotonic() < UntilTime:
        TimeClock.sleep(0.05)
    assert not IsProcessAlive(ProcessId), ProcessId
