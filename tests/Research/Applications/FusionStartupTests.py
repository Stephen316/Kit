import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import KRepoRoot


# a disposable macos process drives the actual pinned bootstrap event handler
@TestMark.skipif(
    System.platform != "darwin", reason="macOS vendor startup and process identity"
)
def CheckBootProof(TmpPath: FilePath) -> None:
    ScriptPath = KRepoRoot / "re/automation/ApplicationWorkers/FusionStartupFixture.py"
    Outcome = Subprocess.run(
        [System.executable, "-B", str(ScriptPath), str(TmpPath.resolve())],
        capture_output=True,
        text=True,
        check=False,
        timeout=110,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    assert JsonCodec.loads(Outcome.stdout) == {
        "vendor_startup": True,
        "manual_refused": True,
        "loading_refused": True,
        "wrong_peer_refused": True,
        "manifest_change_refused": True,
        "fresh_receipts": 2,
    }
