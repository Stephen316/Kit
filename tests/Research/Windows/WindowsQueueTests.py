import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Windows.RunQueueClient import RunQueueClient
from tests.Research.Windows.RunQueueHost import RunQueueHost


# windows request completion must preserve process identity and retain publication custody across host restart
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinQueue(TmpPath: FilePath) -> None:
    Harness = DispatchHost(TmpPath)
    with RunQueueHost(Harness) as Previous:
        assert str(Previous["started"]).startswith("windows:")
        Response = RunQueueClient(Harness, "handoff")
        assert Response["host"] == Previous
        assert Response["status"] == "completed"
        FenceFile = Harness.Endpoint / "fence.json"
        FenceData = FenceFile.read_bytes()
        FenceInfo = JsonCodec.loads(FenceData)
        assert FenceInfo["reason"] == "acceptance_required"
        assert FenceInfo["restart_handoff"]["host"] == Previous
        Duplicate = Harness.StartHost()
        _, ErrorText = Duplicate.communicate(timeout=15)
        assert Duplicate.returncode != 0 and "BlockingIOError" in ErrorText
    with RunQueueHost(Harness) as Current:
        assert Current != Previous
        assert FenceFile.read_bytes() == FenceData
        Blocked = RunQueueClient(Harness)
        assert Blocked["outcome"] == "waiting_application"
        assert Blocked["native_qualified"] is False
        assert len(list(Harness.Endpoint.glob("jobs/*/fixture.bin"))) == 1


# competing clients must not acquire the same installation while its first phase is still running
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinClient(TmpPath: FilePath) -> None:
    Harness = DispatchHost(TmpPath)
    with RunQueueHost(Harness):
        Client = Harness.StartClient("wait", Seconds=45)
        try:
            _ = Harness.WaitFile("entered.json")
            Duplicate = Harness.StartClient()
            _, ErrorText = Duplicate.communicate(timeout=15)
            assert Duplicate.returncode != 0 and "BlockingIOError" in ErrorText
        finally:
            (Harness.Endpoint / "release.json").touch()
            Output, ErrorText = Client.communicate(timeout=20)
        assert Client.returncode == 0, ErrorText
        assert JsonCodec.loads(Output)["status"] == "completed"


# a lock aliased to another file must not become the endpoint ownership record
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinLink(TmpPath: FilePath) -> None:
    Harness = DispatchHost(TmpPath)
    Outside = TmpPath / "Other.bin"
    Content = b"unrelated file must remain unchanged"
    _ = Outside.write_bytes(Content)
    (Harness.Endpoint / "host.lock").hardlink_to(Outside)
    Process = Harness.StartHost()
    try:
        _, ErrorText = Process.communicate(timeout=15)
        assert Process.returncode != 0
        assert "lock must be a regular file with one link" in ErrorText
        assert Outside.read_bytes() == Content
    finally:
        (Harness.Endpoint / "stop-fixture").touch()
        _ = Process.communicate(timeout=35)
