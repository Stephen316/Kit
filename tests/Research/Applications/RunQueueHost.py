import json as JsonCodec
from collections.abc import Iterator as IterItems
from contextlib import contextmanager as ContextManager

from tests.Research.Applications.DispatchHost import DispatchHost


# the fixture must expose and stop the serving interpreter when its launcher has a different identity
@ContextManager
def RunQueueHost(
    Harness: DispatchHost, Operation: str = "host"
) -> IterItems[dict[str, object]]:
    StopFile = Harness.Endpoint / "stop-fixture"
    ReadyFile = Harness.Endpoint / "ready.json"
    StopFile.unlink(missing_ok=True)
    ReadyFile.unlink(missing_ok=True)
    Process = Harness.StartHost(Operation)
    try:
        _ = Harness.WaitFile("ready.json")
        RecordInfo: dict[str, dict[str, object]] = JsonCodec.loads(
            ReadyFile.read_text(encoding="utf-8")
        )
        yield RecordInfo["host"]
    finally:
        StopFile.touch()
        Output, ErrorText = Process.communicate(timeout=35)
        assert Process.returncode == 0, Output + ErrorText
