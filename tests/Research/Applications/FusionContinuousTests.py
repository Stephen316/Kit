import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot
from tests.Research.Applications.FusionPhaseQueueTests import (
    MakeQueueHost,
    PreparePair,
    RunFusionTool,
)
from tests.Research.SupervisorClient import SessionHost

# genuine acknowledgement execution stays in the ordinary supervisor child
KFixture = KRepoRoot / "re/automation/ApplicationWorkers/FusionContinuousFixture.py"


# both pairs use the same owner configuration and real durable queue
def PrepareTwo(Dispatch: DispatchHost) -> tuple[SessionHost, FilePath, list[str]]:
    Prepared = Dispatch.RootPath / "Prepared"
    PlanInfo = PreparePair(Prepared, False)
    Harness = MakeQueueHost(Dispatch.RootPath, PlanInfo["source_revision"])
    InstallInfo = JsonCodec.loads(Dispatch.ConfigFile.read_bytes())
    InstallInfo.update(endpoint=str(Dispatch.Endpoint), macos_automatic_quit=True)
    _ = Dispatch.ConfigFile.write_text(JsonCodec.dumps(InstallInfo), encoding="utf-8")
    Inbox = Dispatch.RootPath / "Inbox"
    Inbox.mkdir(mode=0o700)
    Identifiers: list[str] = []
    for RunName in ("first-cycle", "second-cycle"):
        Identifiers.extend(QueueCycle(Harness, Prepared, Inbox, RunName))
    _ = RunFusionTool(
        "re/automation/Controller.py",
        [
            "--store",
            str(Harness.StorePath),
            "resource",
            "application:fusion:local",
            "--capacity",
            "1",
            "--available",
        ],
    )
    return Harness, Inbox, Identifiers


# distinct run labels preserve each receipt even when the trusted plan is the same
def QueueCycle(
    Harness: SessionHost, Prepared: FilePath, Inbox: FilePath, RunName: str
) -> list[str]:
    ResultText = RunFusionTool(
        "re/automation/ApplicationWorkers/QueueFusionPhases.py",
        [
            "--config",
            str(Harness.ConfigFile),
            "--plan",
            str(Prepared / "plan.json"),
            "--resource",
            "application:fusion:local",
            "--owner-lifecycle",
            "--receipt",
            str(Inbox / f"{RunName}.json"),
            "--run",
            RunName,
        ],
    )
    JobNames = CastValue(dict[str, str], JsonCodec.loads(ResultText)["jobs"])
    return [JobNames["a"], JobNames["b"]]


# the fixture runner differs only in its application body while sharing state and custody
def FixtureConfig(Dispatch: DispatchHost, Harness: SessionHost) -> FilePath:
    RegistryPath = Dispatch.RootPath / "FixtureRunners.json"
    Registry = JsonCodec.loads((Dispatch.RootPath / "Runners.json").read_bytes())
    Registry["runners"]["capture.fusion"]["argv"] = [
        System.executable,
        "-B",
        str(KFixture),
        "worker",
        str(Dispatch.ConfigFile),
        "{session}",
    ]
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    ConfigPath = Dispatch.RootPath / "FixtureSupervisor.json"
    Settings = JsonCodec.loads(Harness.ConfigFile.read_bytes())
    Settings["registry"] = str(RegistryPath)
    _ = ConfigPath.write_text(JsonCodec.dumps(Settings), encoding="utf-8")
    return ConfigPath


# log files let the parent inspect failure output without filling child pipes
def StartFixture(
    Dispatch: DispatchHost, ModeName: str, *Arguments: str
) -> "Subprocess.Popen[str]":
    LogPath = Dispatch.RootPath / f"{ModeName}.log"
    with LogPath.open("w", encoding="utf-8") as LogFile:
        return Subprocess.Popen(
            [System.executable, "-B", str(KFixture), ModeName, *Arguments],
            stdout=LogFile,
            stderr=Subprocess.STDOUT,
            text=True,
        )


# owner progress is complete only when the exact number of final receipts is durable
def WaitFinal(Dispatch: DispatchHost, Expected: int, Drained: bool = False) -> None:
    Expires = TimeClock.monotonic() + 25
    while TimeClock.monotonic() < Expires:
        Found = [
            ItemPath
            for ItemPath in Dispatch.Endpoint.glob("fusion-lifecycle-*.json")
            if ItemPath.name != "fusion-lifecycle-active.json"
        ]
        Active = Dispatch.Endpoint / "fusion-lifecycle-active.json"
        if len(Found) == Expected and (not Drained or not Active.exists()):
            return
        TimeClock.sleep(0.04)
    raise AssertionError((Dispatch.RootPath / "owner.log").read_text(encoding="utf-8"))


# accepted phase b must remain reserved until both the endpoint and intent drain
def ReplayAck(
    Dispatch: DispatchHost, Harness: SessionHost, JobNames: list[str]
) -> None:
    _ = Dispatch.WaitFile("ack-first-lost")
    WaitFinal(Dispatch, 1)
    Fence = Dispatch.Endpoint / "fence.json"
    assert Harness.ReadJob(JobNames[1])["state"] == "completed"
    assert JsonCodec.loads(Fence.read_bytes())["reason"] == "acceptance_required"
    assert Harness.ReadJob(JobNames[2])["attempts"] == 0
    (Dispatch.Endpoint / "ack-allow-cleanup").touch()
    _ = Dispatch.WaitFile("ack-cleaned-lost")
    assert not Fence.exists()
    assert not (Dispatch.Endpoint / "acceptance-journal.json").exists()
    assert not list((Dispatch.Endpoint / "jobs").iterdir())
    assert Harness.ReadJob(JobNames[2])["attempts"] == 0
    assert (Dispatch.Endpoint / "fusion-lifecycle-active.json").is_file()
    (Dispatch.Endpoint / "ack-allow-replay").touch()
    _ = Dispatch.WaitFile("ack-replayed")
    WaitFinal(Dispatch, 2, Drained=True)


# both accepted phases must show the planned consecutive owned process boundaries
def VerifyTwo(Harness: SessionHost, JobNames: list[str]) -> None:
    Epochs: list[object] = []
    for JobName in JobNames:
        Current = Harness.ReadJob(JobName)
        assert Current["state"] == "completed" and Current["attempts"] == 1
        Outcome = CastValue(dict[str, object], Harness.ReadResult(JobName)["result"])
        Records = CastValue(dict[str, object], Outcome["records"])
        Epochs.append(Records["host"])
    assert Epochs[0] != Epochs[1] == Epochs[2] != Epochs[3]


# bounded fixture shutdown preserves diagnostics and leaves no serving child behind
def StopFixture(
    Dispatch: DispatchHost, Processes: list["Subprocess.Popen[str]"]
) -> None:
    for Child in reversed(Processes):
        if Child.poll() is None:
            Child.terminate()
    for Child in reversed(Processes):
        try:
            _ = Child.wait(timeout=8)
        except Subprocess.TimeoutExpired:
            Child.kill()
            _ = Child.wait(timeout=3)
    (Dispatch.Endpoint / "stop-fixture").touch()
    Ready = Dispatch.Endpoint / "ready.json"
    if Ready.is_file():
        Stopped = Dispatch.WaitFile("host-stopped.json")
        assert JsonCodec.loads(Stopped.read_bytes()) == JsonCodec.loads(
            Ready.read_bytes()
        )


# one supervisor and one owner loop process both pairs after uncertain acknowledgement replies
@TestMark.skipif(
    System.platform != "darwin", reason="macOS Fusion owner acknowledgement"
)
def CheckTwoPairs(TmpPath: FilePath) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Inbox, JobNames = PrepareTwo(Dispatch)
    Settings = FixtureConfig(Dispatch, Harness)
    Lifecycle = Inbox / "Lifecycle.json"
    _ = Lifecycle.write_text("disposable owner profile\n", encoding="utf-8")
    Processes = [StartFixture(Dispatch, "host", str(Dispatch.ConfigFile))]
    try:
        Dispatch.WaitHost(Processes[0].pid)
        Processes.append(
            StartFixture(
                Dispatch,
                "owner",
                "--config",
                str(Harness.ConfigFile),
                "--installation",
                str(Dispatch.ConfigFile),
                "--lifecycle",
                str(Lifecycle),
                "--queue-directory",
                str(Inbox),
                "--poll-seconds",
                "1",
            )
        )
        Processes.append(
            StartFixture(
                Dispatch,
                "supervisor",
                str(Dispatch.Endpoint),
                JobNames[1],
                "--config",
                str(Settings),
                "run",
                "--max-seconds",
                "90",
            )
        )
        ReplayAck(Dispatch, Harness, JobNames)
        VerifyTwo(Harness, JobNames)
    finally:
        StopFixture(Dispatch, Processes)
