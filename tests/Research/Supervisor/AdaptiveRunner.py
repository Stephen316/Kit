import json as JsonCodec
import signal as Signals
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


def RunAdaptive() -> None:
    SessionPath = FilePath(System.argv[1])
    JobText = (SessionPath / "job.json").read_text(encoding="utf-8")
    SessionInfo = JsonCodec.loads(JobText)
    Options = SessionInfo["job"]["options"]
    if Options.get("mode") == "deadline":
        _ = Signals.signal(Signals.SIGTERM, Signals.SIG_IGN)
        TimeClock.sleep(120)
        return
    TimeClock.sleep(float(Options.get("hold_seconds", 1)))
    ResultInfo: dict[str, object] = {
        "outcome": "completed",
        "reason": "adaptive fixture finished",
        "records": {
            "count": 1,
            "inputs": [],
            "tokenless": "lease_token" not in JobText,
        },
    }
    _ = (SessionPath / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )


if __name__ == "__main__":
    RunAdaptive()
