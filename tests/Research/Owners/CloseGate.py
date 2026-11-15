import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.Owners.KillOwner import KillOwner
from tests.Research.Owners.OwnerBarriers import WaitRecord
from tests.Research.Owners.ReadParent import ReadParent


def CloseGate(GateRoot: FilePath) -> None:
    _ = (GateRoot / "Release").write_text("release", encoding="ascii")
    HeldFile = GateRoot / "Held.json"
    if not HeldFile.is_file():
        return
    HeldInfo = JsonCodec.loads(HeldFile.read_text(encoding="utf-8"))
    try:
        _ = WaitRecord(GateRoot / "Result.json")
        Until = TimeClock.monotonic() + 15
        while (
            ReadParent(int(HeldInfo["gate_pid"])) is not None
            and TimeClock.monotonic() < Until
        ):
            TimeClock.sleep(0.05)
    finally:
        if ReadParent(int(HeldInfo["gate_pid"])) is not None:
            KillOwner(int(HeldInfo["gate_pid"]), Required=False)
