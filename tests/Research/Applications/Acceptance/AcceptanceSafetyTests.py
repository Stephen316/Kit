import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.Acceptance.AcceptanceHost import AcceptanceHost


# tampered and superseded results must leave their original evidence available for investigation
def CheckAckRefusal() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = AcceptanceHost(FilePath(TempPath).resolve())
        Server = Harness.Dispatch.StartHost()
        try:
            Harness.Dispatch.WaitHost(Server.pid)
            Spool = Harness.Accept()
            Fence = Harness.Dispatch.Endpoint / "fence.json"
            OriginalFence = Fence.read_bytes()
            Output = Spool / "fixture.bin"
            Original = Output.read_bytes()
            _ = Output.write_bytes(b"tampered retained bytes")
            _ = Harness.Reconcile(ExitCode=1)
            assert Output.read_bytes() == b"tampered retained bytes"
            assert Fence.read_bytes() == OriginalFence
            _ = Output.write_bytes(Original)
            Harness.Supervisor.BindBytes("source", b"superseded inputs")
            assert Harness.Supervisor.ReadJob(Harness.JobName)["state"] != "completed"
            _ = Harness.Reconcile(ExitCode=1)
            assert Output.read_bytes() == Original
            assert Fence.read_bytes() == OriginalFence
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)


# acknowledgement may release custody but an old application must remain fenced until restart
def CheckAckRestart() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = AcceptanceHost(FilePath(TempPath).resolve(), "handoff")
        OldHost = Harness.Dispatch.StartHost()
        try:
            Harness.Dispatch.WaitHost(OldHost.pid)
            Spool = Harness.Accept()
            Result = Harness.Reconcile()
            assert Result["status"] == "acknowledged"
            assert Result["restart_retained"] is True
            assert not Spool.exists()
            Fence = Harness.Dispatch.Endpoint / "fence.json"
            Restart = Fence.read_bytes()
            assert JsonCodec.loads(Restart)["reason"] == "restart_required"
            assert Harness.Reconcile()["status"] == "no_pending_acceptance"
            assert Fence.read_bytes() == Restart
            Blocked = Harness.Dispatch.StartClient()
            Output, ErrorText = Blocked.communicate(timeout=15)
            assert Blocked.returncode == 0, ErrorText
            assert JsonCodec.loads(Output)["outcome"] == "waiting_application"
        finally:
            OldHost.terminate()
            _ = OldHost.communicate(timeout=15)
        AssertNewHost(Harness)


# a late acknowledgement must preserve a different spool admitted by the new process
def AssertNewHost(Harness: AcceptanceHost) -> None:
    Current = Harness.Dispatch.StartHost()
    try:
        Harness.Dispatch.WaitHost(Current.pid)
        Client = Harness.Dispatch.StartClient()
        Output, ErrorText = Client.communicate(timeout=15)
        assert Client.returncode == 0, ErrorText
        assert JsonCodec.loads(Output)["status"] == "completed"
        _ = Harness.Reconcile(ExitCode=1)
        assert len(list((Harness.Dispatch.Endpoint / "jobs").iterdir())) == 1
    finally:
        Current.terminate()
        _ = Current.communicate(timeout=15)
