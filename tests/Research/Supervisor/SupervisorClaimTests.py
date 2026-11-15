import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.SupervisorClient import FixtureJob, InitStore, SessionHost


# status publication can lag a real transaction so wait for the actual reported decision
def WaitRefusal(Harness: SessionHost, ShowRefusal: bool) -> dict[str, object]:
    Until = TimeClock.monotonic() + 30
    while TimeClock.monotonic() < Until:
        Status = JsonCodec.loads(Harness.RunCli("status"))
        Decision = Status["pools"]["second"]["capacity"]["decision"]
        if (
            isinstance(Decision, dict)
            and ("controller_refusal" in Decision) is ShowRefusal
        ):
            return CastValue(dict[str, object], Decision)
        TimeClock.sleep(0.1)
    raise AssertionError(
        "second pool did not expose the expected controller refusal state"
    )


# both pools must have local headroom so the second pool reaches the real controller ceiling
def ClaimHost(RootPath: FilePath) -> SessionHost:
    Harness = SessionHost(
        RootPath,
        {"first": 1, "second": 1},
        {"fixture.first": "first", "fixture.second": "second"},
        InitStore(RootPath / "Store", 1),
    )
    RegistryFile = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    for RunnerInfo in Registry["runners"].values():
        RunnerInfo["initial_peak_memory_mib"] = 64
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    Harness.SubmitJobs(
        [
            FixtureJob(
                "held:first",
                "fixture.first",
                max_attempts=1,
                lease_seconds=30,
                options={"mode": "sleep-first"},
            ),
            FixtureJob("held:second", "fixture.second", max_attempts=1),
        ]
    )
    return Harness


# committed claim refusal must be visible without consuming an attempt for the queued job
def WitnessClaimCap(RootPath: FilePath) -> None:
    Harness = ClaimHost(RootPath)
    Worker = Harness.StartRun("--idle-seconds", "6", "--max-seconds", "65")
    try:
        _ = Harness.WaitSession("held:first")
        Refused = WaitRefusal(Harness, True)
        assert Refused["controller_refusal"] == {
            "adapter": "a03",
            "reason": "concurrency limit",
        }
        assert Refused["active_limit"] == Refused["calculated_capacity"] == 1
        assert Refused["reason"] is None
        Delayed = Harness.ReadJob("held:second")
        assert Delayed["state"] == "queued" and Delayed["attempts"] == 0
        _ = Harness.RunCli("pause", "first", "--reason", "release test occupancy")
        _ = WaitRefusal(Harness, False)
        Output, ErrorText = Worker.communicate(timeout=55)
        assert Worker.returncode == 0, ErrorText
    finally:
        if Worker.poll() is None:
            Worker.terminate()
            _ = Worker.communicate(timeout=20)
    Completed = Harness.ReadJob("held:second")
    assert Completed["state"] == "completed" and Completed["attempts"] == 1
    Events = [JsonCodec.loads(LineText) for LineText in Output.splitlines()]
    Refusals = [
        Event
        for Event in Events
        if Event.get("event") == "controller_claim_refused"
        and Event["pool"] == "second"
    ]
    assert len(Refusals) == 1
    assert (
        Refusals[0]["adapter"] == "a03" and Refusals[0]["reason"] == "concurrency limit"
    )


# the direct controller subprocess must report the refusal from its actual claim transaction
def CheckClaimCap(TmpPath: FilePath) -> None:
    WitnessClaimCap(TmpPath)
