import json as JsonCodec
import os as OsLayer
import sys as System
from pathlib import Path as FilePath

from tests.Research.Windows.RunChild import RunChild
from tests.Research.Windows.StartChild import StartChild


def RunWindows() -> None:
    if System.argv[1] == "child":
        RunChild()
        return
    SessionPath = FilePath(System.argv[1])
    SessionInfo = JsonCodec.loads(
        (SessionPath / "job.json").read_text(encoding="utf-8")
    )
    Options: dict[str, str] = SessionInfo["job"]["options"]
    assert OsLayer.environ["TEMP"] == str(SessionPath / "work")
    assert OsLayer.environ["TMP"] == str(SessionPath / "work")
    assert OsLayer.environ["USERPROFILE"] == str(SessionPath / "work")
    assert "SystemRoot" in OsLayer.environ
    if Options["mode"] == "flood":
        _ = System.stdout.buffer.write(b"stdout" * (4096 * 256))
        _ = System.stderr.buffer.write(b"stderr" * (4096 * 256))
        _ = System.stdout.buffer.flush()
        _ = System.stderr.buffer.flush()
    else:
        StartChild(Options)
    ResultInfo: dict[str, object] = {
        "outcome": "completed",
        "reason": "Windows process fixture finished",
        "records": {
            "count": 1,
            "inputs": [],
            "tokenless": "lease_token" not in SessionInfo,
        },
    }
    _ = (SessionPath / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )


if __name__ == "__main__":
    RunWindows()
