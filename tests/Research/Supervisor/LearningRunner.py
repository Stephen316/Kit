import json as JsonCodec
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


# the estimator needs a measurable memory sample from a successful real child process
def RunLearning() -> None:
    SessionPath = FilePath(System.argv[1])
    JobText = (SessionPath / "job.json").read_text(encoding="utf-8")
    Content = bytearray(2 * 1048576)
    for Offset in range(0, len(Content), 4096):
        Content[Offset] = 1
    TimeClock.sleep(1)
    ResultInfo: dict[str, object] = {
        "outcome": "completed",
        "reason": "measured fixture finished",
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
    RunLearning()
