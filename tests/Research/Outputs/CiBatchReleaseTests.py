import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot


# frozen batches must publish all exact successor bindings or leave the ledger untouched
def CheckRelease(TmpPath: FilePath) -> None:
    Program = KRepoRoot / "re/automation/CiBatchReleaseFixture.py"
    Response = Subprocess.run(
        [System.executable, str(Program), str(TmpPath)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Response.returncode == 0, Response.stderr
    assert JsonCodec.loads(Response.stdout) == {
        "released_members": 2,
        "exact_resume": True,
        "stale_batch_untouched": True,
    }
