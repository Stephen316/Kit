import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchWait import DispatchWait
from tests.Research.WindowsRecords.RecordProcess import (
    CheckBlocked,
    KFixture,
    RunRecord,
)

KWindowsOnly = TestMark.skipif(
    System.platform != "win32", reason="Windows file handles"
)


@KWindowsOnly
def CheckRewritten() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Result = RunRecord("rewritten", FilePath(TempPath).resolve())
        assert Result["size"] == len(
            b'{"version":1,"immutable":true,"rewritten":true}\n'
        )
        assert Result["path_ctime_ns"] != Result["handle_ctime_ns"]


@KWindowsOnly
def CheckUnsafe() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Result = RunRecord("unsafe", FilePath(TempPath).resolve())
        assert Result == {
            "hardlinks": 2,
            "reparse_paths": 2,
            "directory": True,
            "byte_limit": True,
        }


@KWindowsOnly
def CheckMetadata() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Target = FilePath(str(RunRecord("prepare", RootPath)["path"]))
        assert RunRecord("metadata", Target) == {"change_time_rejected": True}


@KWindowsOnly
def CheckSharing() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve() / "Private"
        Target = FilePath(str(RunRecord("prepare", RootPath)["path"]))
        with Subprocess.Popen(
            [System.executable, str(KFixture), "hold", str(Target)],
            stdin=Subprocess.PIPE,
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            text=True,
        ) as Reader:
            try:
                _ = DispatchWait(RootPath).WaitFile("ready")
                Result = RunRecord("mutations", Target)
                print(JsonCodec.dumps(Result, sort_keys=True), flush=True)
                CheckBlocked(Result)
                Stdout, Stderr = Reader.communicate("release\n", timeout=15)
                assert Reader.returncode == 0, Stdout + Stderr
            finally:
                if Reader.poll() is None:
                    Reader.kill()
                    _ = Reader.communicate(timeout=15)
        assert RunRecord("unlocked", Target) == dict.fromkeys(Result, True), Result
        assert (
            Target.read_bytes() == b'{"version":1,"immutable":true,"rewritten":true}\n'
        )
