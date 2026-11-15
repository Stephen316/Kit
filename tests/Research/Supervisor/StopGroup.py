import os as OsLayer
import signal as Signals

from tests.Research.SupervisorClient import IsGoneByTimeout


def StopGroup(ParentId: int | None, ChildId: int | None) -> None:
    if ParentId is not None:
        try:
            OsLayer.killpg(ParentId, Signals.SIGKILL)
        except ProcessLookupError:
            pass
    if ChildId is not None and not IsGoneByTimeout(ChildId, Timeout=1):
        OsLayer.kill(ChildId, Signals.SIGKILL)
