import json as JsonCodec
from collections.abc import Iterator as IterItems
from contextlib import contextmanager as ContextManager

from tests.Research.Applications.DispatchHost import DispatchHost


# windows fixture shutdown must release the actual interpreter even when its launcher has a different identity
@ContextManager
def RunQueueHost(Harness: DispatchHost) -> IterItems[dict[str, object]]:
    StopFile = Harness.Endpoint / "stop-fixture"
    ReadyFile = Harness.Endpoint / "ready.json"
    StopFile.unlink(missing_ok=True)
    ReadyFile.unlink(missing_ok=True)
    Process = Harness.StartHost()
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
