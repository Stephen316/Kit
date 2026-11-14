import hashlib as Hashing
import json as JsonCodec
import signal as Signals
import sys as System
import time as TimeClock
from pathlib import Path as FilePath


def WriteResult(SessionPath: FilePath, JobInfo: dict[str, object]) -> int:
    JobText = (SessionPath / "job.json").read_text(encoding="utf-8")
    Session = JsonCodec.loads(JobText)
    Digests: list[str] = []
    for RoleName in sorted(Session["inputs"]):
        InputInfo = Session["inputs"][RoleName]
        Content = (SessionPath / str(InputInfo["path"])).read_bytes()
        assert Hashing.sha256(Content).hexdigest() == InputInfo["sha256"]
        Digests.append(str(InputInfo["sha256"]))
    Options = JsonCodec.loads(JsonCodec.dumps(JobInfo["options"]))
    Records = Options.get("records", {"count": 1})
    Records["inputs"] = Digests
    Records["tokenless"] = "lease_token" not in JobText
    ResultInfo = {
        "outcome": str(Options.get("outcome", "completed")),
        "reason": "fixture runner finished",
        "records": Records,
    }
    _ = (SessionPath / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )
    return 0


def HoldInput(SessionPath: FilePath) -> bool:
    Session = JsonCodec.loads((SessionPath / "job.json").read_text(encoding="utf-8"))
    return any(
        (SessionPath / str(InputInfo["path"])).read_bytes().startswith(b"hold")
        for InputInfo in Session["inputs"].values()
    )


def RunFixture() -> int:
    SessionPath = FilePath(System.argv[1])
    Session = JsonCodec.loads((SessionPath / "job.json").read_text(encoding="utf-8"))
    JobInfo: dict[str, object] = Session["job"]
    Options = JsonCodec.loads(JsonCodec.dumps(JobInfo["options"]))
    ModeName = str(Options.get("mode", "complete"))
    if ModeName == "invalid":
        _ = (SessionPath / "result.json").write_text(
            JsonCodec.dumps({"outcome": "completed"}), encoding="utf-8"
        )
        return 0
    if ModeName == "crash":
        _ = System.stderr.write("fixture failure\n")
        return 3
    if ModeName == "ignore-term":
        _ = Signals.signal(Signals.SIGTERM, Signals.SIG_IGN)
        TimeClock.sleep(120)
        return 0
    if ModeName == "sleep-first" and int(Session["attempt"]) == 1:
        TimeClock.sleep(120)
    if ModeName == "hold" and HoldInput(SessionPath):
        TimeClock.sleep(120)
    return WriteResult(SessionPath, JobInfo)


if __name__ == "__main__":
    System.exit(RunFixture())
