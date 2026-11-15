from json import loads as LoadJson
from pathlib import Path as FilePath
from time import monotonic as ReadClock, sleep as WaitBriefly


# contention assertions must wait until the supervisor has persisted a real worker session
def WaitSession(WorkPath: FilePath) -> None:
    Deadline = ReadClock() + 30
    while ReadClock() < Deadline:
        for RecordPath in (WorkPath / "SupervisorState/sessions").glob(
            "*/session.json"
        ):
            try:
                Record = LoadJson(RecordPath.read_bytes())
            except (OSError, ValueError):
                continue
            if Record.get("job_id") == "cli:hold":
                return
        WaitBriefly(0.1)
    raise AssertionError("no configured worker session started")
