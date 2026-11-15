import hashlib as Hashing
import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import KRepoRoot


# the normal appkit entry point must consult the disposable application delegate
@TestMark.skipif(System.platform != "darwin", reason="macOS AppKit quit boundary")
@TestMark.parametrize("CaseName", ("accept", "cancel", "cancel-reply-loss"))
def CheckAppKitQuit(TmpPath: FilePath, CaseName: str) -> None:
    ScriptPath = (
        KRepoRoot / "re/automation/ApplicationWorkers/AppKitQuitDelegateFixture.py"
    )
    RunResult = Subprocess.run(
        [System.executable, "-B", str(ScriptPath), str(TmpPath.resolve()), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=65,
    )
    assert RunResult.returncode == 0, RunResult.stderr
    Evidence = JsonCodec.loads(RunResult.stdout)
    assert Evidence == JsonCodec.loads((TmpPath / "ExitObservation.json").read_bytes())
    assert Evidence["case"] == CaseName
    BridgePath = ScriptPath.with_name("MacCocoaQuit.py")
    assert (
        Evidence["bridge_sha256"] == Hashing.sha256(BridgePath.read_bytes()).hexdigest()
    )
    assert Evidence["missing_application_refused"] is True
    assert Evidence["non_main_thread_refused"] is True
    Accepts = CaseName == "accept"
    assert Evidence["delegate_decision"] == ("accept" if Accepts else "cancel")
    assert (Evidence["kernel_exit"] is not None) is Accepts
    assert (Evidence["will_terminate_sha256"] is not None) is Accepts
    assert Evidence["duplicate_refused"] is (not Accepts)
    if CaseName != "accept":
        assert Evidence["returned_receipt_present"] is (CaseName == "cancel")
