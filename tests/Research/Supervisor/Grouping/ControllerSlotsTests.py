import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Supervisor.Grouping.BatchHost import WriteBatchReg
from tests.Research.Supervisor.Grouping.BatchRecords import BatchEvents, BatchJobs
from tests.Research.SupervisorClient import FixtureJob, InitStore, SessionHost


# the shared cap must cover a real grouped worker and an independent singleton pool
def SharedHost(RootPath: FilePath) -> SessionHost:
    Harness = SessionHost(
        RootPath,
        {"decode": 1, "second": 2},
        {"fixture.decode": "decode", "fixture.second": "second"},
        InitStore(RootPath / "Store", 4),
    )
    WriteBatchReg(RootPath)
    Harness.BindBytes("source", b"shared controller slots")
    Harness.SubmitJobs(
        BatchJobs(
            3,
            lease_seconds=30,
            timeout_seconds=100,
            max_attempts=1,
            options={"hold_seconds": 90},
        )
    )
    return Harness


# the status file can lag the transaction while the owner refreshes its shared headroom
def WaitSlotView(
    Harness: SessionHost, RunningJobs: int, PhysicalSessions: int
) -> tuple[dict[str, object], dict[str, object]]:
    Until = TimeClock.monotonic() + 22
    while TimeClock.monotonic() < Until:
        Pools = JsonCodec.loads(Harness.RunCli("status"))["pools"]
        Decision = CastValue(
            dict[str, object], Pools["second"]["capacity"]["decision"] or {}
        )
        Capacity = CastValue(dict[str, object], Decision.get("controller_capacity", {}))
        if (
            Capacity.get("running_jobs") == RunningJobs
            and Capacity.get("physical_sessions") == PhysicalSessions
        ):
            assert Capacity["maximum_running_jobs"] == 4
            assert Capacity["available_jobs"] == 4 - RunningJobs
            SampleAge = Capacity["age_seconds"]
            assert isinstance(SampleAge, (int, float)) and 0 <= SampleAge <= 5
            return Decision, Capacity
        TimeClock.sleep(0.1)
    raise AssertionError(f"no pool decision with {RunningJobs} logical jobs")


# both singleton jobs must enter while the group still holds three leases
def FillSlots(Harness: SessionHost) -> None:
    Harness.SubmitJobs(
        [
            FixtureJob(
                "slot:active",
                "fixture.second",
                lease_seconds=30,
                timeout_seconds=100,
                max_attempts=1,
                options={"mode": "sleep-first"},
            ),
            FixtureJob("slot:waiting", "fixture.second", max_attempts=1),
        ]
    )
    _ = Harness.WaitSession("slot:active")


# a numeric zero must coincide with an actual refusal while local capacity remains available
def AssertFull(Harness: SessionHost) -> None:
    FullView, FullCap = WaitSlotView(Harness, 4, 1)
    assert FullView["active_limit"] == 2 and FullView["reason"] is None
    assert FullView["controller_refusal"] == {
        "adapter": "a03",
        "reason": "concurrency limit",
    }
    assert FullCap["effective_capacity"] == 1
    assert FullCap["effective_active_limit"] == 1
    assert FullCap["effective_additional_sessions"] == 0
    Waiting = Harness.ReadJob("slot:waiting")
    assert Waiting["state"] == "queued" and Waiting["attempts"] == 0


# after release the delayed job must complete using the existing claim and settlement path
def AssertRestored(Harness: SessionHost) -> None:
    _ = Harness.RunCli("pause", "decode", "--reason", "release grouped leases")
    Restored, RestoredCap = WaitSlotView(Harness, 1, 1)
    assert "controller_refusal" not in Restored
    assert RestoredCap["effective_additional_sessions"] == 1
    Completed = Harness.ReadJob("slot:waiting")
    assert Completed["state"] == "completed" and Completed["attempts"] == 1


# a group can exhaust shared controller room while another pool has local physical headroom
def CheckSharedCap(TmpPath: FilePath) -> None:
    Harness = SharedHost(TmpPath)
    SupervisorRun = Harness.StartRun("--idle-seconds", "2", "--max-seconds", "115")
    try:
        _ = Harness.WaitSession("batch:00")
        Before, BeforeCap = WaitSlotView(Harness, 3, 0)
        assert Before["active_limit"] == 2
        assert BeforeCap["effective_additional_sessions"] == 1

        FillSlots(Harness)
        AssertFull(Harness)
        AssertRestored(Harness)
        _ = Harness.RunCli("pause", "second", "--reason", "release singleton lease")
        Output, ErrorText = SupervisorRun.communicate(timeout=25)
        assert SupervisorRun.returncode == 0, ErrorText
    finally:
        if SupervisorRun.poll() is None:
            SupervisorRun.terminate()
            _ = SupervisorRun.communicate(timeout=20)
    Events: list[object] = [
        JsonCodec.loads(LineText) for LineText in Output.splitlines()
    ]
    assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
        3,
        1,
        1,
    ]
