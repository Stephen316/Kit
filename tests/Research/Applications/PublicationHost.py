import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

# publication fixtures must resolve consistently even when writer processes use private working directories
KRepoRoot = FilePath(__file__).resolve().parents[3]

# race checks need the same real publisher for contenders and observers
KFixturePath = KRepoRoot / "re/automation/ApplicationWorkers/PublicationFixture.py"


# independent publisher processes are required to exercise concurrent destination acquisition
def StartPublish(RootPath: FilePath, WriterName: str) -> Subprocess.Popen[str]:
    return Subprocess.Popen(
        [
            System.executable,
            str(KFixturePath),
            "publish",
            "--root",
            str(RootPath),
            "--writer",
            WriterName,
        ],
        stdin=Subprocess.PIPE,
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )


# contenders must share a release barrier so scheduling does not serialize away the publication race
def ReleaseWriters(Processes: list[Subprocess.Popen[str]]) -> None:
    for Process in Processes:
        assert Process.stdin is not None
        _ = Process.stdin.write("x")
        _ = Process.stdin.flush()


# a losing or failed publisher must not survive beyond its fixture lifetime
def StopPublishers(Processes: list[Subprocess.Popen[str]]) -> None:
    for Process in Processes:
        if Process.poll() is None:
            Process.kill()
        _ = Process.communicate(timeout=15)
