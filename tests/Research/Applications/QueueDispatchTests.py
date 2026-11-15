import hashlib as Hashing
import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.RetainedRestart import AssertRetained


# client process completion must be tied to a response from the sole endpoint owner
def CheckRound() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        Server = Harness.StartHost()
        try:
            _ = Harness.WaitFile("ready.json")
            Client = Harness.StartClient()
            Output, ErrorText = Client.communicate(timeout=30)
            assert Client.returncode == 0, ErrorText
            Response = JsonCodec.loads(Output)
            assert Response["status"] == "completed", Response
            assert Response["proof"] == {
                "claim": "transport_fixture",
                "native_qualified": False,
            }
            Artifact = Response["files"]["fixture"]
            Files = list(Harness.Endpoint.glob("jobs/*/fixture.bin"))
            assert len(Files) == 1
            assert (
                Hashing.sha256(Files[0].read_bytes()).hexdigest() == Artifact["sha256"]
            )
            Duplicate = Harness.StartHost()
            _, ErrorText = Duplicate.communicate(timeout=15)
            assert Duplicate.returncode != 0
            assert "BlockingIOError" in ErrorText
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)


# persistent ownership after host replacement must stay fenced until the retained application is handled
def CheckRestart() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        First = Harness.StartHost()
        try:
            _ = Harness.WaitFile("ready.json")
            Client = Harness.StartClient("handoff")
            Output, ErrorText = Client.communicate(timeout=30)
            assert Client.returncode == 0, ErrorText
            Handoff = JsonCodec.loads(Output)["proof"]["restart_handoff"]
            assert Handoff["host"]["pid"] == First.pid
            assert Handoff["owner"] == "external_application_owner"
            Blocked = Harness.StartClient()
            Output, ErrorText = Blocked.communicate(timeout=30)
            assert Blocked.returncode == 0, ErrorText
            assert JsonCodec.loads(Output)["outcome"] == "waiting_application"
        finally:
            First.terminate()
            _ = First.communicate(timeout=15)
        AssertRetained(Harness, First.pid)
