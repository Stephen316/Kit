import hashlib as HashCodec
import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import IsGoneByTimeout


def CheckTrial(TrialPath: FilePath, Requested: int, SourcePath: FilePath) -> None:
    Prepared = JsonCodec.loads(
        (TrialPath / "Prepared.json").read_text(encoding="utf-8")
    )
    Registry = JsonCodec.loads((TrialPath / "Runners.json").read_text(encoding="utf-8"))
    Contract = JsonCodec.loads(
        (TrialPath / "RegistryContract.json").read_text(encoding="utf-8")
    )
    ConfigInfo = JsonCodec.loads(
        (TrialPath / "Supervisor.json").read_text(encoding="utf-8")
    )
    Cleanup = JsonCodec.loads((TrialPath / "Cleanup.json").read_text(encoding="utf-8"))
    assert Prepared["controller_max_running"] == Requested
    assert Prepared["resources"] == {"offline:slot": {"capacity": 1, "available": True}}
    assert ConfigInfo["pools"]["offline"]["max_sessions"] == Requested
    assert ConfigInfo["adaptive_limits"] is False
    assert (
        Contract["single_job_per_session"] is True
        and Contract["runtime_group_protocol"] is None
    )
    assert not any(
        NameValue.startswith("group_")
        for NameValue in Registry["runners"]["decode.fusion"]
    )
    assert (
        Contract["sha256"]
        == HashCodec.sha256((TrialPath / "Runners.json").read_bytes()).hexdigest()
    )
    assert Cleanup["sessions_empty"] is True and Cleanup["claims_empty"] is True
    assert not tuple((TrialPath / "State" / "sessions").iterdir())
    assert not tuple((TrialPath / "State" / "claims").iterdir())
    assert IsGoneByTimeout(Cleanup["supervisor_pid"])
    SourceHash = HashCodec.sha256(SourcePath.read_bytes()).hexdigest()
    assert (
        TrialPath / "Controller" / "objects" / SourceHash[:2] / SourceHash
    ).read_bytes() == SourcePath.read_bytes()
