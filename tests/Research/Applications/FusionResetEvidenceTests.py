import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import KRepoRoot


# the report must verify native peer identity and accepted historical receipts across processes
@TestMark.skipif(
    System.platform != "darwin", reason="Darwin application process identity"
)
def CheckResetProof(TmpPath: FilePath) -> None:
    ScriptPath = (
        KRepoRoot / "re/automation/ApplicationWorkers/FusionResetEvidenceFixture.py"
    )
    Process = Subprocess.run(
        [System.executable, "-B", str(ScriptPath), str(TmpPath.resolve())],
        capture_output=True,
        text=True,
        check=False,
        timeout=65,
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    Outcome = JsonCodec.loads(Process.stdout)
    assert Outcome["scope"] == "fusion_corroborated_completed_native_requests"
    assert Outcome["corroborated"] == 2
    assert Outcome["duplicate_dispatches"] == 1
    assert Outcome["other_peers"] == 1
    assert Outcome["unattributed_completions"] == 1
    assert Outcome["verified_count_reaches_limit"] is True
