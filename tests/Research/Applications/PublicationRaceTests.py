import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Applications.PublicationHost import (
    KFixturePath,
    ReleaseWriters,
    StartPublish,
    StopPublishers,
)


def CheckRecordRace() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Observer = Subprocess.Popen(
            [System.executable, str(KFixturePath), "observe", "--root", str(RootPath)],
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            text=True,
        )
        Processes = [StartPublish(RootPath, f"writer:{Index}") for Index in range(6)]
        try:
            ReleaseWriters(Processes)
            Outcomes: list[dict[str, object]] = []
            for Process in Processes:
                Output, ErrorText = Process.communicate(timeout=60)
                assert Process.returncode == 0, ErrorText
                Outcomes.append(JsonCodec.loads(Output))
            Output, ErrorText = Observer.communicate(timeout=60)
            assert Observer.returncode == 0, ErrorText
            Published = [
                Record for Record in Outcomes if Record["outcome"] == "published"
            ]
            assert len(Published) == 1
            assert sum(Record["outcome"] == "exists" for Record in Outcomes) == 5
            assert JsonCodec.loads(Output)["writer"] == Published[0]["writer"]
            assert len(list(RootPath.iterdir())) == 1
        finally:
            StopPublishers(Processes + [Observer])


def CheckRecordKept() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        TargetPath = RootPath / "winner.json"
        _ = TargetPath.write_bytes(b"preexisting destination bytes")
        Writer = StartPublish(RootPath, "replacement:forbidden")
        try:
            Output, ErrorText = Writer.communicate(input="x", timeout=60)
            assert Writer.returncode == 0, ErrorText
            assert JsonCodec.loads(Output)["outcome"] == "exists"
            assert TargetPath.read_bytes() == b"preexisting destination bytes"
            assert TargetPath.stat().st_nlink == 1
            assert len(list(RootPath.iterdir())) == 1
        finally:
            StopPublishers([Writer])
