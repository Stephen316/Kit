import hashlib as Hashing
import json as JsonCodec
import shutil as FileTree
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost


# crashes during result copying must preserve recoverable evidence without making duplicate native work
def CheckCopyCrash() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = DispatchHost(FilePath(TempPath).resolve())
        Server = Harness.StartHost()
        try:
            Harness.WaitHost(Server.pid)
            Client = Harness.StartClient("copied", Seconds=20)
            Copied = JsonCodec.loads(
                Harness.WaitFile("copied.json").read_text(encoding="utf-8")
            )
            WorkPath = FilePath(Copied["work"])
            SpoolPath = FilePath(Copied["spool"])
            Digest = Copied["artifacts"]["fixture"]["sha256"]
            assert (
                Hashing.sha256((WorkPath / "fixture.bin").read_bytes()).hexdigest()
                == Digest
            )
            Client.kill()
            _ = Client.communicate(timeout=15)
            FileTree.rmtree(WorkPath.parent)
            assert (
                Hashing.sha256((SpoolPath / "fixture.bin").read_bytes()).hexdigest()
                == Digest
            )
            Pending = JsonCodec.loads(
                (SpoolPath / "pending-acceptance.json").read_text(encoding="utf-8")
            )
            assert Pending["acknowledgement"] == "pending_controller_acceptance"
            assert Pending["files"]["fixture"]["sha256"] == Digest
            Blocked = Harness.StartClient()
            Output, ErrorText = Blocked.communicate(timeout=15)
            assert Blocked.returncode == 0, ErrorText
            assert JsonCodec.loads(Output)["outcome"] == "waiting_application"
            assert len(list((Harness.Endpoint / "jobs").iterdir())) == 1
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)
