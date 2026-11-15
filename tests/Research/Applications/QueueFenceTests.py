import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost


# expired callers must not leave completed outputs after their request loses authority
def CheckDeadClient() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        Client = Harness.StartClient("queued", Seconds=30)
        try:
            RequestPath = Harness.WaitRequest(Client)
        finally:
            if Client.poll() is None:
                Client.kill()
            _ = Client.communicate(timeout=15)
        Server = Harness.StartHost()
        try:
            DonePath = Harness.WaitFile(
                str(RequestPath.with_suffix(".done").relative_to(Harness.Endpoint))
            )
            Response = JsonCodec.loads(DonePath.read_text(encoding="utf-8"))
            assert Response["status"] == "expired", Response
            assert Response["files"] == {}
            assert not (RequestPath.parent / "fixture.bin").exists()
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)


# late worker bytes cannot become a valid result after the transport fences the request
def CheckLateResult() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        Server = Harness.StartHost()
        try:
            _ = Harness.WaitFile("ready.json")
            Client = Harness.StartClient("wait", Seconds=8)
            Entered = JsonCodec.loads(
                Harness.WaitFile("entered.json").read_text(encoding="utf-8")
            )
            WorkPath = FilePath(Entered["work"])
            Output, ErrorText = Client.communicate(timeout=20)
            assert Client.returncode == 0, ErrorText
            assert JsonCodec.loads(Output)["outcome"] == "waiting_application"
            assert WorkPath.is_dir()
            assert (WorkPath / "phase.running").is_file()
            _ = (Harness.Endpoint / "release.json").write_text("{}", encoding="utf-8")
            DonePath = Harness.WaitFile(
                str((WorkPath / "phase.done").relative_to(Harness.Endpoint))
            )
            Response = JsonCodec.loads(DonePath.read_text(encoding="utf-8"))
            assert Response["status"] == "expired", Response
            assert Response["files"] == {}
            assert (WorkPath / "fixture.bin").is_file()
            assert (Harness.Endpoint / "fence.json").is_file()
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)
