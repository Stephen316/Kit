import json as JsonCodec
import subprocess as Subprocess
import time as WallClock
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost


# a held fence must have the exact identity issued by the first host
def WriteHandoff(Harness: DispatchHost, HostId: int) -> FilePath:
    Harness.WaitHost(HostId)
    Ready = JsonCodec.loads((Harness.Endpoint / "ready.json").read_bytes())
    PlanHash = "f" * 64
    Handoff = {
        "installation": "fixture:installation",
        "job_id": "e" * 32,
        "reason": "restart_required",
        "host": Ready["host"],
        "plan_sha256": PlanHash,
        "at": WallClock.time(),
        "owner": "external_application_owner",
    }
    InputPath = Harness.RootPath / "Restart.json"
    Records = {"host": Ready["host"], "restart_handoff": Handoff}
    _ = InputPath.write_text(
        JsonCodec.dumps({"records": Records, "plan_sha256": PlanHash}), encoding="utf-8"
    )
    _ = (Harness.Endpoint / "fence.json").write_text(
        JsonCodec.dumps(Handoff), encoding="utf-8"
    )
    return InputPath


# the wait fixture executes restart admission without running a cad host
def StartWait(
    Harness: DispatchHost, InputPath: FilePath, Seconds: int
) -> "Subprocess.Popen[str]":
    return Subprocess.Popen(
        Harness.Command
        + [
            "restart",
            "--installation",
            str(Harness.ConfigFile),
            "--session",
            str(InputPath),
            "--seconds",
            str(Seconds),
        ],
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )


# cleanup captures diagnostics while respecting an already exited fixture process
def StopProcess(Process: "Subprocess.Popen[str]") -> None:
    if Process.poll() is None:
        Process.terminate()
    _ = Process.communicate(timeout=15)


# the fixture writes one structured disposition for each real invocation
def ReadWait(Process: "Subprocess.Popen[str]") -> dict[str, str]:
    Output, ErrorText = Process.communicate(timeout=20)
    assert Process.returncode == 0, ErrorText
    Result: dict[str, str] = JsonCodec.loads(Output)
    return Result


# a fresh owner can clear the fence after the original process has actually exited
def CheckFreshWait(TmpPath: FilePath) -> None:
    Harness = DispatchHost(TmpPath.resolve())
    First = Harness.StartHost()
    try:
        InputPath = WriteHandoff(Harness, First.pid)
        Waiter = StartWait(Harness, InputPath, 25)
        try:
            _ = Harness.WaitFile("restart-wait.json")
            assert Waiter.poll() is None
            assert (Harness.Endpoint / "fence.json").is_file()
            assert list((Harness.Endpoint / "jobs").iterdir()) == []
            StopProcess(First)
            Second = Harness.StartHost()
            try:
                Harness.WaitHost(Second.pid)
                assert ReadWait(Waiter) == {"status": "ready"}
            finally:
                StopProcess(Second)
        finally:
            StopProcess(Waiter)
    finally:
        StopProcess(First)


# replacement ownership alone cannot retire a restart fence after an unsuccessful bootstrap
def CheckNativeGate(TmpPath: FilePath) -> None:
    Harness = DispatchHost(TmpPath.resolve())
    First = Harness.StartHost()
    try:
        _ = WriteHandoff(Harness, First.pid)
        FencePath = Harness.Endpoint / "fence.json"
        Before = FencePath.read_bytes()
    finally:
        StopProcess(First)
    for StageName in ("startup-unverified", "startup-stale"):
        assert ObserveStartup(Harness, StageName) == {"before": True, "after": True}
        assert FencePath.read_bytes() == Before
        assert list((Harness.Endpoint / "jobs").iterdir()) == []
    assert ObserveStartup(Harness, "startup-verified") == {
        "before": True,
        "after": False,
    }
    assert not FencePath.exists()


# each startup observation needs a separate real process and the production native provider
def ObserveStartup(Harness: DispatchHost, StageName: str) -> dict[str, bool]:
    Terminal = Subprocess.run(
        Harness.Command + [StageName, "--installation", str(Harness.ConfigFile)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Terminal.returncode == 0, Terminal.stderr
    StatusInfo: dict[str, bool] = JsonCodec.loads(Terminal.stdout)
    return StatusInfo


# deadline and invalid restart states must prevent admission
def CheckParkWait(TmpPath: FilePath) -> None:
    Harness = DispatchHost(TmpPath.resolve())
    Server = Harness.StartHost()
    try:
        InputPath = WriteHandoff(Harness, Server.pid)
        Expired = ReadWait(StartWait(Harness, InputPath, 1))
        assert Expired["status"] == "waiting_application"
        assert "dispatch deadline" in Expired["reason"]
        AssertBadFence(Harness, InputPath)
    finally:
        StopProcess(Server)


# a foreign fence cannot authorize the requested restart
def AssertBadFence(Harness: DispatchHost, InputPath: FilePath) -> None:
    FencePath = Harness.Endpoint / "fence.json"
    Fence = JsonCodec.loads(FencePath.read_bytes())
    Fence["job_id"] = "a" * 32
    _ = FencePath.write_text(JsonCodec.dumps(Fence), encoding="utf-8")
    Different = ReadWait(StartWait(Harness, InputPath, 12))
    assert Different["status"] == "waiting_application"
    assert "another application disposition" in Different["reason"]
    FencePath.unlink()
    Missing = ReadWait(StartWait(Harness, InputPath, 12))
    assert Missing["status"] == "waiting_application"
    assert "has not exited" in Missing["reason"]
    Evidence = JsonCodec.loads(InputPath.read_bytes())
    Evidence["records"]["restart_handoff"]["owner"] = "untrusted"
    _ = InputPath.write_text(JsonCodec.dumps(Evidence), encoding="utf-8")
    Malformed = ReadWait(StartWait(Harness, InputPath, 12))
    assert Malformed["status"] == "rejected"
    assert "no valid restart handoff" in Malformed["reason"]
