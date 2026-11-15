import os as OsLayer
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Applications.Acceptance.AcceptanceHost import AcceptanceHost


# a real filesystem refusal must leave a durable journal that can resume after the interruption
@Pytest.mark.skipif(
    OsLayer.name == "nt" or OsLayer.geteuid() == 0,
    reason="requires an unprivileged posix process",
)
def CheckAckResume() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = AcceptanceHost(FilePath(TempPath).resolve(), "resume")
        Server = Harness.Dispatch.StartHost()
        try:
            Harness.Dispatch.WaitHost(Server.pid)
            Spool = Harness.Accept()
            Nested = Spool / "nested"
            Nested.chmod(0o500)
            try:
                _ = Harness.Reconcile(ExitCode=1)
                assert (Nested / "fixture.bin").is_file()
                Journal = Harness.Dispatch.Endpoint / "acceptance-journal.json"
                assert Journal.is_file()
                assert (Harness.Dispatch.Endpoint / "fence.json").is_file()
            finally:
                Nested.chmod(0o700)
            assert Harness.Reconcile()["status"] == "acknowledged"
            assert not Spool.exists()
            assert not Journal.exists()
            assert not (Harness.Dispatch.Endpoint / "fence.json").exists()
            assert Harness.Reconcile()["status"] == "no_pending_acceptance"
        finally:
            Server.terminate()
            _ = Server.communicate(timeout=15)
