import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import KRepoRoot


# a disposable app exercises launches through appkit with an exact executable and live peer guard
@TestMark.skipif(
    System.platform != "darwin", reason="macOS LaunchServices process boundary"
)
def CheckMacLaunch(TmpPath: FilePath) -> None:
    ScriptPath = KRepoRoot / "re/automation/ApplicationWorkers/MacReplacementFixture.py"
    RunResult = Subprocess.run(
        [System.executable, "-B", str(ScriptPath), str(TmpPath.resolve())],
        capture_output=True,
        text=True,
        check=False,
        timeout=190,
    )
    assert RunResult.returncode == 0, RunResult.stderr
    Evidence = JsonCodec.loads(RunResult.stdout)
    assert Evidence["peer"]["pid"] > 0
    assert Evidence["source_pin_refused"] is True
    assert Evidence["fence_change_refused"] is True
    assert Evidence["duplicate_refused"] is True
