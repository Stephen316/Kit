import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Supervisor.AdaptiveHost import MakeAdaptive
from tests.Research.Supervisor.Reserve.ReserveHost import (
    MakeReserveHost,
    ReserveChild,
    WaitReserve,
)
from tests.Research.Supervisor.Reserve.ReserveMemory import (
    KAllocMib,
    IsHosted,
    RequireRoom,
)
from tests.Research.Supervisor.Reserve.ReserveReport import VerifyReserve
from tests.Research.SupervisorClient import FixtureJob


# low memory must suspend admission before the supervisor consumes a queued attempt
def CheckLowReserve() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = MakeAdaptive(FilePath(TempPath))
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["reserved_memory_mib"] = 1048576
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs(
            [FixtureJob("adaptive:reserve", "fixture.decode", max_attempts=1)]
        )
        Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle(IdleSeconds=2)))
        Admissions = [Event for Event in Events if Event.get("event") == "admission"]
        assert len(Admissions) == 1
        assert Admissions[0]["adaptive_reason"] == "memory_headroom"
        assert Admissions[0]["active_limit"] == 0
        assert (
            Admissions[0]["host"]["available_memory_bytes"]
            < Admissions[0]["reserved_memory_bytes"]
        )
        Blocked = Harness.ReadJob("adaptive:reserve")
        assert Blocked["state"] == "queued"
        assert Blocked["attempts"] == 0


# an actual host reserve crossing must halve an established target without stopping current jobs
@Pytest.mark.skipif(
    not IsHosted(), reason="requires the opted in GitHub hosted Linux runner"
)
def CheckMemDrop(TmpPath: FilePath) -> None:
    try:
        ReserveMib = RequireRoom() - 224
    except (OSError, ValueError) as Error:
        Pytest.skip(f"ambient reserve crossing unmeasured: {Error}")
    Harness = MakeReserveHost(TmpPath, ReserveMib)
    Running = Harness.StartRun("--idle-seconds", "2", "--max-seconds", "70")
    try:
        InitialTime, InitialRev = WaitReserve(Harness, 2, 4)
        with ReserveChild(ReserveMib) as Allocation:
            assert Allocation["rss_mib"] >= Allocation["mib"] == KAllocMib
            assert Allocation["loaded_mib"] < ReserveMib < Allocation["before_mib"]
            LowTime, ReducedRev = WaitReserve(Harness, 1, 2, InitialTime)
            assert ReducedRev == InitialRev + 1
            HeldTime, HeldRev = WaitReserve(Harness, 1, 2, LowTime)
            assert HeldRev == ReducedRev
        _, RestoredRev = WaitReserve(Harness, 1, 4, HeldTime)
        assert RestoredRev == ReducedRev
        Output, ErrorText = Running.communicate(timeout=55)
        assert Running.returncode == 0, ErrorText
    finally:
        if Running.poll() is None:
            Running.terminate()
            _ = Running.communicate(timeout=15)
    for JobName in ("reserve:first", "reserve:second"):
        JobInfo = Harness.ReadJob(JobName)
        assert JobInfo["state"] == "completed" and JobInfo["attempts"] == 1
    VerifyReserve(Output, ReserveMib, ReducedRev, Allocation)
