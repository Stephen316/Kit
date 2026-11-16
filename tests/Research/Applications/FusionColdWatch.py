import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from collections.abc import Iterator as ItemIterator
from contextlib import contextmanager as HoldContext
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot
from tests.Research.Applications.FusionPhaseQueueTests import RunFusionTool


# each fixture observer uses the real continuing owner and retains its bounded output
@HoldContext
def RunOwner(
    Dispatch: DispatchHost, Flags: list[str], Label: str
) -> ItemIterator[FilePath]:
    LogPath = Dispatch.RootPath / f"{Label}.log"
    ScriptPath = KRepoRoot / "re/automation/ApplicationWorkers/FusionLifecycleOwner.py"
    with LogPath.open("w", encoding="utf-8") as LogFile:
        Child = Subprocess.Popen(
            [
                System.executable,
                "-B",
                str(ScriptPath),
                *Flags,
                "--queue-directory",
                str(Dispatch.RootPath),
                "--poll-seconds",
                "1",
            ],
            stdout=LogFile,
            stderr=Subprocess.STDOUT,
            text=True,
        )
        try:
            yield LogPath
        finally:
            if Child.poll() is None:
                Child.terminate()
            try:
                _ = Child.wait(timeout=5)
            except Subprocess.TimeoutExpired:
                Child.kill()
                _ = Child.wait(timeout=5)


# the subprocess is ready only after its exact watch or exit report becomes visible
def AwaitStatus(LogPath: FilePath, Expected: str) -> dict[str, object]:
    Expires = TimeClock.monotonic() + 12
    while TimeClock.monotonic() < Expires:
        Content = LogPath.read_text(encoding="utf-8")
        for RecordLine in Content.split("\n")[:-1]:
            Report: dict[str, object] = JsonCodec.loads(RecordLine)
            if Report["status"] == Expected:
                return Report
        TimeClock.sleep(0.03)
    raise AssertionError(LogPath.read_text(encoding="utf-8")[-4096:])


# a new owner can rearm a live peer but must never substitute absence for a kernel event
def VerifyColdWatch(
    Dispatch: DispatchHost, Flags: list[str], AdmissionHash: str
) -> None:
    ExitPath = Dispatch.Endpoint / f"initial-native-exit-{AdmissionHash}.json"
    with RunOwner(Dispatch, Flags, "FirstOwner") as LogPath:
        First = AwaitStatus(LogPath, "commissioned_exit_watch_armed")
    assert not ExitPath.exists()
    with RunOwner(Dispatch, Flags, "NextOwner") as LogPath:
        Second = AwaitStatus(LogPath, "commissioned_exit_watch_armed")
        assert Second["watch_sha256"] != First["watch_sha256"]
        _ = RunFusionTool(
            "re/automation/ApplicationWorkers/FusionColdStartFixture.py",
            ["cleanup", str(Dispatch.RootPath), str(Dispatch.Endpoint)],
        )
        Report = AwaitStatus(LogPath, "commissioned_native_exit_observed")
        AssertExit(Dispatch, ExitPath, AdmissionHash, Report, Second["watch_sha256"])
    VerifyLostWatch(Dispatch, Flags, ExitPath)


# the terminal bytes must name the admitted peer and the exact second observing process
def AssertExit(
    Dispatch: DispatchHost,
    ExitPath: FilePath,
    Admission: str,
    Report: dict[str, object],
    WatchDigest: object,
) -> None:
    RawBytes = ExitPath.read_bytes()
    Result = JsonCodec.loads(RawBytes)
    Launch = JsonCodec.loads((Dispatch.Endpoint / "cold-start-peer.json").read_bytes())
    assert Report["exit_sha256"] == HashBytes(RawBytes).hexdigest()
    assert Result["observation"] == "darwin_process_exit_event"
    assert Result["watch_sha256"] == WatchDigest
    assert Result["disposition"] == "outside_owner_scheduled_quit"
    assert Result["epoch"]["admission_sha256"] == Admission
    assert Result["epoch"]["peer"] == Launch["peer"]


# a later process with only the old watch intents cannot recreate a missing exit
def VerifyLostWatch(
    Dispatch: DispatchHost, Flags: list[str], ExitPath: FilePath
) -> None:
    Withheld = ExitPath.with_suffix(".withheld")
    _ = ExitPath.rename(Withheld)
    try:
        with RunOwner(Dispatch, Flags, "LostOwner") as LogPath:
            _ = AwaitStatus(LogPath, "commissioned_native_exit_unobserved")
            assert not ExitPath.exists()
    finally:
        _ = Withheld.rename(ExitPath)
