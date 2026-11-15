import json as JsonCodec
import subprocess as Subprocess
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot


# untrusted request changes must be rejected before the application fixture writes any evidence
def CheckRevision() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        Client = Harness.StartClient("queued", Seconds=30)
        try:
            RequestPath = Harness.WaitRequest(Client)
        except BaseException:
            if Client.poll() is None:
                Client.kill()
            _ = Client.communicate(timeout=15)
            raise
        Request = JsonCodec.loads(RequestPath.read_text(encoding="utf-8"))
        Request["source_revision"] = Subprocess.run(
            ["git", "-C", str(KRepoRoot), "rev-parse", "HEAD^"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        ).stdout.strip()
        _ = RequestPath.write_text(JsonCodec.dumps(Request), encoding="utf-8")
        Server = Harness.StartHost()
        try:
            _ = Harness.WaitFile(
                str(RequestPath.with_suffix(".rejected").relative_to(Harness.Endpoint))
            )
            assert not (RequestPath.parent / "fixture.bin").exists()
            assert not RequestPath.with_suffix(".done").exists()
        finally:
            Client.terminate()
            _ = Client.communicate(timeout=15)
            Server.terminate()
            _ = Server.communicate(timeout=15)


# unexpected request fields must not expand the fixed application dispatch boundary
def CheckFixedEntry() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        Server = Harness.StartHost("counterpart")
        try:
            _ = Harness.WaitFile("ready.json")
            Client = Harness.StartClient()
            Output, ErrorText = Client.communicate(timeout=30)
            assert Client.returncode == 0, ErrorText
            Response = JsonCodec.loads(Output)
            assert Response["outcome"] == "waiting_application", Response
            assert "unsupported fields" in Response["reason"]
            assert not list(Harness.Endpoint.glob("jobs/*/fixture.bin"))
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)
