import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

KRepoRoot = FilePath(__file__).resolve().parents[3]
KFixturePath = KRepoRoot / "re/automation/ApplicationWorkers/PublicationFixture.py"


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


def ReleaseWriters(Processes: list[Subprocess.Popen[str]]) -> None:
    for Process in Processes:
        assert Process.stdin is not None
        _ = Process.stdin.write("x")
        _ = Process.stdin.flush()


def StopPublishers(Processes: list[Subprocess.Popen[str]]) -> None:
    for Process in Processes:
        if Process.poll() is None:
            Process.kill()
        _ = Process.communicate(timeout=15)
