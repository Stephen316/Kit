import json as JsonCodec
import os as OsLayer
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.SetAppRunner import SetAppRunner
from tests.Research.SupervisorClient import FixtureJob, KRepoRoot, SessionHost


# an independent installed copy allows tamper checks without mutating the real checkout
def InstallStub(
    TmpPath: FilePath, Queue: DispatchHost
) -> tuple[FilePath, bytes, dict[str, str]]:
    Config = JsonCodec.loads(Queue.ConfigFile.read_text(encoding="utf-8"))
    Config["windows_phase_a"] = True
    _ = Queue.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
    Captures = KRepoRoot / "re/automation/PairedCaptures"
    Installed = TmpPath / "KitCaptureRunner.py"
    ExactBootstrap = (
        Captures / "Runner/KitCaptureRunner/KitCaptureRunner.py"
    ).read_bytes()
    _ = Installed.write_bytes(ExactBootstrap)
    HomePath = TmpPath / "AppData/KitCaptureRunner"
    HomePath.mkdir(parents=True)
    _ = (HomePath / "config.json").write_text(
        JsonCodec.dumps(
            {"allowed_root": str(Captures), "dispatch": str(Queue.ConfigFile)}
        ),
        encoding="utf-8",
    )
    return (
        Installed,
        ExactBootstrap,
        dict(OsLayer.environ, APPDATA=str(HomePath.parent)),
    )


# the admission probe needs a real pinned plan bound through the controller store
def PrepareQueue(TmpPath: FilePath, Queue: DispatchHost) -> SessionHost:
    Prepared = TmpPath / "Prepared"
    Preparation = Subprocess.run(
        [
            System.executable,
            "-I",
            "-S",
            str(KRepoRoot / "re/automation/PairedCaptures/FusionFreshProcess.py"),
            "--output",
            str(Prepared),
            "--recipe",
            "P01",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Preparation.returncode == 0, Preparation.stderr
    Harness = SessionHost(TmpPath, {"apps": 1}, {"fixture.app": "apps"})
    SetAppRunner(Harness, Queue.ConfigFile)
    Harness.BindBytes("plan", (Prepared / "plan.json").read_bytes())
    Harness.SubmitJobs(
        [
            FixtureJob(
                f"phase-{Phase}",
                "fixture.app",
                lease_seconds=55,
                resources=["application:missing"] if Phase == "a" else [],
                options={"phase": Phase},
                inputs={"plan": "plan"},
            )
            for Phase in ("a", "b")
        ]
    )
    return Harness


# refusal is proven at the native readiness gate without publishing any cad evidence
def AssertWaiting(Harness: SessionHost, Queue: DispatchHost) -> None:
    PhaseA = Harness.ReadJob("phase-a")
    assert PhaseA["state"] == "waiting_application", PhaseA
    assert "exclusive Fusion host has open documents" in str(PhaseA["reason"])
    PhaseB = Harness.ReadJob("phase-b")
    assert PhaseB["state"] == "waiting_application", PhaseB
    assert "Windows Fusion only admits ordinary Phase A" in str(PhaseB["reason"])
    for Phase in ("a", "b"):
        Result = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult(f"phase-{Phase}")))
        assert "output_artifacts" not in Result
        assert Result["result"]["records"]["native_qualified"] is False
    Probes = list(Queue.Endpoint.glob("jobs/*/probe.done"))
    assert len(Probes) == 1
    Response = JsonCodec.loads(Probes[0].read_bytes())
    assert Response["host"]["started"].startswith("windows:")
    assert Response["proof"] is None and Response["files"] == {}
    Fence = JsonCodec.loads((Queue.Endpoint / "fence.json").read_bytes())
    assert Fence["reason"] == "quarantined" and Fence["host"] == Response["host"]
    assert not (Queue.Endpoint / "grant.json").exists()


# startup refusals must leave the prior addin status and legacy queue untouched
def AssertRefusal(Command: list[str], Environment: dict[str, str], Reason: str) -> None:
    HomePath = FilePath(Environment["APPDATA"]) / "KitCaptureRunner"
    StatusPath = HomePath / "runner.json"
    Before = StatusPath.read_bytes()
    Refused = Subprocess.run(
        Command,
        env=Environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Refused.returncode != 0 and Reason in Refused.stderr
    assert StatusPath.read_bytes() == Before
    assert not (HomePath / "queue").exists()


# the hosted boundary must use the actual installed addin and the actual supervisor dispatch
@Pytest.mark.skipif(System.platform != "win32", reason="Windows Fusion admission")
def CheckWinFusion(TmpPath: FilePath) -> None:
    Queue = DispatchHost(TmpPath)
    Installed, ExactBootstrap, Environment = InstallStub(TmpPath, Queue)
    Harness = PrepareQueue(TmpPath, Queue)
    DoneFlag = TmpPath / "StopFixture"
    Command = [
        System.executable,
        "-I",
        "-S",
        str(FilePath(__file__).with_name("FusionStub.py")),
        str(Installed),
        str(DoneFlag),
    ]
    Child = Subprocess.Popen(
        Command,
        env=Environment,
        text=True,
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
    )
    try:
        _ = Harness.RunIdle(MaxSeconds=75)
        AssertWaiting(Harness, Queue)
    finally:
        DoneFlag.touch()
        try:
            Output, Errors = Child.communicate(timeout=15)
        except Subprocess.TimeoutExpired:
            Child.kill()
            _, _ = Child.communicate(timeout=15)
            raise
    assert Child.returncode == 0, Output + Errors

    _ = Installed.write_bytes(ExactBootstrap + b"\n")
    AssertRefusal(
        Command, Environment, "reload the add-in from the trusted installation revision"
    )
    Config = JsonCodec.loads(Queue.ConfigFile.read_bytes())
    del Config["windows_phase_a"]
    _ = Queue.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
    AssertRefusal(Command, Environment, "Windows Fusion Phase A requires owner opt-in")
