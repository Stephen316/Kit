import json as JsonCodec
import os as OsLayer
import signal as Signals
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


# process tree limits need excess memory in a descendant rather than only in the leader
def RunMemory() -> None:
    SessionPath = FilePath(System.argv[1])
    SessionInfo = JsonCodec.loads(
        (SessionPath / "job.json").read_text(encoding="utf-8")
    )
    ChildId = OsLayer.fork()
    if ChildId == 0:
        _ = Signals.signal(Signals.SIGTERM, Signals.SIG_IGN)
        TimeClock.sleep(0.3)
        Content = bytearray(96 * 1048576)
        for Offset in range(0, len(Content), 4096):
            Content[Offset] = 1
        TimeClock.sleep(120)
        OsLayer._exit(0)
    ChildFile = FilePath(SessionInfo["job"]["options"]["child_pid_path"])
    _ = ChildFile.write_text(str(ChildId), encoding="ascii")
    TimeClock.sleep(120)


if __name__ == "__main__":
    RunMemory()
