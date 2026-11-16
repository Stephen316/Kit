import os as OsLayer
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# process coverage needs isolated files for reproducible native scalar scenarios
def DecodeInchCase(RootPath: FilePath, Keywords: bytes, Resolved: bytes) -> str:
    KeywordFile = RootPath / "Keywords.xml"
    ResolvedFile = RootPath / "Resolved.bin"
    _ = KeywordFile.write_bytes(Keywords)
    _ = ResolvedFile.write_bytes(Resolved)
    Environment = dict(OsLayer.environ)
    RepoPath = FilePath(__file__).resolve().parents[5]
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RepoPath / "src"), str(RepoPath), Environment.get("PYTHONPATH", ""))
    )
    Result = Subprocess.run(
        [
            System.executable,
            str(FilePath(__file__).with_name("NativeRoster.py")),
            str(KeywordFile),
            str(ResolvedFile),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env=Environment,
    )
    assert Result.returncode == 0, Result.stderr
    return Result.stdout
