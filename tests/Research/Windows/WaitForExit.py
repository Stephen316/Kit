import time as TimeClock

from tests.Research.Windows.IsProcessAlive import IsProcessAlive


def WaitForExit(ProcessId: int, Timeout: float = 15) -> None:
    UntilTime = TimeClock.monotonic() + Timeout
    while IsProcessAlive(ProcessId) and TimeClock.monotonic() < UntilTime:
        TimeClock.sleep(0.05)
    assert not IsProcessAlive(ProcessId), ProcessId
