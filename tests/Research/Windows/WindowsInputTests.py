import hashlib as HashLib
import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import KRepoRoot, SessionHost

# a separate interpreter must use the real supervisor adapter without a controller lookup child
KStageProgram = """
import json
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from Adapters import load_adapter

store, owner, digest, destination = sys.argv[2:]
adapter = load_adapter({"adapter": "a03", "store": store}, Path.cwd())
adapter.owner = owner
adapter.command = ["unexpected-artifact-subprocess"]
try:
    size = adapter.FetchInput(digest, Path(destination))
except (OSError, ValueError) as error:
    print(json.dumps({"error": type(error).__name__, "message": str(error)}))
else:
    print(json.dumps({"size": size}))
"""


# each owner rotation must go through the normal controller transaction
def SetStagingOwner(StorePath: FilePath, OwnerToken: str) -> None:
    Result = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(StorePath),
            "rotate-owner",
            "--new-owner",
            OwnerToken,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Result.returncode == 0, Result.stderr


# the child exposes only the adapter lookup and the private bytes staged from its result
def StageInput(
    StorePath: FilePath, OwnerToken: str, Digest: str, Target: FilePath
) -> dict[str, object]:
    Result = Subprocess.run(
        [
            System.executable,
            "-c",
            KStageProgram,
            str(KRepoRoot / "re/automation"),
            str(StorePath),
            OwnerToken,
            Digest,
            str(Target),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Result.returncode == 0, Result.stderr
    Response: dict[str, object] = JsonCodec.loads(Result.stdout)
    return Response


# windows can stage a verified input only under the current durable owner
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinInput(TmpPath: FilePath) -> None:
    Harness = SessionHost(TmpPath, {"decode": 1}, {"fixture.decode": "decode"})
    StorePath = Harness.StorePath
    assert StorePath is not None
    Content = b"artifact content bound through the real controller"
    Harness.BindBytes("source", Content)
    Digest = HashLib.sha256(Content).hexdigest()
    Target = TmpPath / "Staged.bin"
    CurrentOwner = "a" * 64
    ReplacementOwner = "b" * 64
    SetStagingOwner(StorePath, CurrentOwner)
    Database = StorePath / "ledger.sqlite3"
    DatabaseBytes = Database.read_bytes()
    assert StageInput(StorePath, CurrentOwner, Digest, Target) == {"size": len(Content)}
    assert Target.read_bytes() == Content
    assert Database.read_bytes() == DatabaseBytes
    Target.unlink()
    SetStagingOwner(StorePath, ReplacementOwner)
    assert StageInput(StorePath, CurrentOwner, Digest, Target)["error"] == "StaleOwner"
    assert not Target.exists()
    Artifact = StorePath / "objects" / Digest[:2] / Digest
    _ = Artifact.write_bytes(b"tampered")
    Refusal = StageInput(StorePath, ReplacementOwner, Digest, Target)
    assert Refusal["error"] == "ValueError"
    assert "artifact integrity mismatch" in str(Refusal["message"])
    assert not Target.exists()
