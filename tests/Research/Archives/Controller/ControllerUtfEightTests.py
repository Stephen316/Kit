from functools import partial as BindArgs
from hashlib import sha256 as DigestBytes
from importlib.util import (
    module_from_spec as ModuleFromSpec,
    spec_from_file_location as SourceSpec,
)
from json import dumps as EncodeJson, loads as ParseJson
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
import sys as System
from typing import Callable, Protocol, cast as CastValue

from pytest import mark as MarkValue

# real command and adapter processes must consume the same committed implementation sources
KRepoRoot = FilePath(__file__).resolve().parents[4]

# combining characters cannot be represented by the restrictive stdout encoding used by each child
KReason = "completed e\u0301vidence"


# cli processes and the actual bound adapter share one checked variadic invocation contract
class InvokeApi(Protocol):

    # operation arguments retain paths and labels without weakening response typing at either boundary
    def __call__(self, *ArgList: object) -> dict[str, object]: ...


# fixture records use the unchanged canonical utf eight payload representation and immutable digest definition
def WriteRecord(Destination: FilePath, Record: dict[str, object]) -> None:
    Payload = (
        EncodeJson(Record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    assert Destination.write_bytes(Payload) == len(Payload)


# real cli stdout must retain canonical utf eight bytes and one lf despite the process locale settings
def RunCommand(StorePath: FilePath, *ArgList: object) -> dict[str, object]:
    Process = RunProcess(
        [
            System.executable,
            "-B",
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(StorePath),
            *[str(ItemValue) for ItemValue in ArgList],
        ],
        cwd=KRepoRoot,
        capture_output=True,
        check=False,
        timeout=120,
        env={**ProcessEnv, "PYTHONIOENCODING": "ascii:strict", "PYTHONUTF8": "0"},
    )
    if Process.returncode:
        assert Process.stdout == b"" and Process.stderr.endswith(b"\n")
        raise ValueError(Process.stderr.decode("utf-8"))
    Record = CastValue(dict[str, object], ParseJson(Process.stdout.decode("utf-8")))
    assert Process.stderr == b""
    assert Process.stdout == (
        EncodeJson(
            Record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return Record


# the actual adapter transport must decode both child streams explicitly without a fake controller
def MakeAdapter(StorePath: FilePath) -> InvokeApi:
    System.path.insert(0, str(KRepoRoot / "re/automation"))
    SpecValue = SourceSpec(
        "KitUtfEightAdapter", KRepoRoot / "re/automation/Adapters.py"
    )
    assert SpecValue is not None and SpecValue.loader is not None
    Module = ModuleFromSpec(SpecValue)
    SpecValue.loader.exec_module(Module)
    Construct = CastValue(Callable[[dict[str, str]], object], Module.A03Adapter)
    Adapter = Construct({"store": str(StorePath)})
    return CastValue(InvokeApi, getattr(Adapter, "Invoke"))


# a durable unicode claim acknowledgement must identify the one actual attempt and leave its lease usable
def SeedClaim(Invoke: InvokeApi, RootPath: FilePath) -> FilePath:
    assert Invoke("init")["store_version"] == 4
    JobPath = RootPath / "Job.json"
    WriteRecord(
        JobPath,
        {
            "id": "utf-eight-job",
            "kind": "fixture.inspect",
            "inputs": {},
            "rule_version": "rule@1",
            "tool_version": "tool@1",
            "max_attempts": 1,
            "lease_seconds": 300,
            "timeout_seconds": 300,
            "options": {"note": KReason},
        },
    )
    assert Invoke("submit", JobPath)
    ClaimPath = RootPath / "Claim-e\u0301.json"
    Claimed = Invoke("claim", "--worker", "worker:utf-eight", "--claim-file", ClaimPath)
    assert Claimed == {
        "job": "utf-eight-job",
        "attempt": 1,
        "claim_file": str(ClaimPath),
    }
    Lease = CastValue(dict[str, object], ParseJson(ClaimPath.read_bytes()))
    assert Lease["attempt"] == 1
    assert CastValue(dict[str, object], Lease["job"])["options"] == {"note": KReason}
    assert Invoke("heartbeat", "--lease", ClaimPath)["job_id"] == "utf-eight-job"
    return ClaimPath


# an actual output intake refusal must remain decodable and must not consume the accepted claim
def RefuseOutput(Invoke: InvokeApi, RootPath: FilePath, ClaimPath: FilePath) -> None:
    try:
        _ = Invoke("unsupported-e\u0301")
    except ValueError as Problem:
        assert "invalid choice" in str(Problem) and "unsupported-e\u0301" in str(
            Problem
        )
    else:
        raise AssertionError("unknown unicode command must be refused")
    WorkPath = RootPath / "work"
    WorkPath.mkdir()
    ResultPath = RootPath / "BadResult.json"
    WriteRecord(
        ResultPath,
        {
            "result": {
                "outcome": "completed",
                "artifacts": {
                    "proof": {
                        "path": "missing-e\u0301.bin",
                        "size_bytes": 0,
                        "sha256": DigestBytes(b"").hexdigest(),
                    }
                },
            }
        },
    )
    try:
        _ = Invoke(
            "finish",
            "--lease",
            ClaimPath,
            "--result",
            ResultPath,
            "--outcome",
            "completed",
            "--reason",
            KReason,
            "--output-root",
            WorkPath,
        )
    except ValueError as Problem:
        assert "controller invalid output:" in str(Problem)
    else:
        raise AssertionError("missing declared output must be refused")
    Running = CastValue(
        list[dict[str, object]], Invoke("status", "--job", "utf-eight-job")["jobs"]
    )[0]
    assert Running["state"] == "running" and Running["attempts"] == 1
    assert Running["result"] is None
    assert Invoke("heartbeat", "--lease", ClaimPath)["job_id"] == "utf-eight-job"


# completion and artifact lookup must retain unicode reasons and hashes from the unchanged canonical payload
def FinishClaim(
    Invoke: InvokeApi, RootPath: FilePath, ClaimPath: FilePath
) -> dict[str, object]:
    ResultPath = RootPath / "Result.json"
    Result: dict[str, object] = {"observation": KReason, "value": 17}
    WriteRecord(ResultPath, Result)
    Finished = Invoke(
        "finish",
        "--lease",
        ClaimPath,
        "--result",
        ResultPath,
        "--outcome",
        "completed",
        "--reason",
        KReason,
    )
    JobValue = CastValue(list[dict[str, object]], Finished["jobs"])[0]
    assert JobValue["state"] == "completed" and JobValue["attempts"] == 1
    assert JobValue["reason"] == KReason
    Expected = EncodeJson(
        Result, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert JobValue["result"] == DigestBytes(Expected).hexdigest()
    Artifact = Invoke("artifact", JobValue["result"])
    assert FilePath(CastValue(str, Artifact["path"])).read_bytes() == Expected
    Receipt = Invoke("artifact", JobValue["receipt"])
    Payload = FilePath(CastValue(str, Receipt["path"])).read_bytes()
    assert DigestBytes(Payload).hexdigest() == JobValue["receipt"]
    Record = CastValue(dict[str, object], ParseJson(Payload))
    assert Record["result_sha256"] == JobValue["result"] and Record["reason"] == KReason
    assert Invoke("events", "--after", "0")["next_after"] is None
    return JobValue


# standalone mode selection exercises actual command and actual adapter boundaries with isolated stores
def ObserveMode(RootPath: FilePath, ModeName: str) -> dict[str, object]:
    StorePath = RootPath / "State-e\u0301"
    Invoke = (
        MakeAdapter(StorePath)
        if ModeName == "adapter"
        else BindArgs(RunCommand, StorePath)
    )
    ClaimPath = SeedClaim(Invoke, RootPath)
    RefuseOutput(Invoke, RootPath, ClaimPath)
    return FinishClaim(Invoke, RootPath, ClaimPath)


# restrictive parent stdout must not turn a successful unicode controller operation into a lost acknowledgement
@MarkValue.parametrize("ModeName", ("cli", "adapter"))
def CheckTransport(TmpPath: FilePath, ModeName: str) -> None:
    Process = RunProcess(
        [
            System.executable,
            "-B",
            "-m",
            "tests.Research.Archives.Controller.ControllerUtfEightTests",
            str(TmpPath),
            ModeName,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        check=False,
        timeout=180,
        env={**ProcessEnv, "PYTHONIOENCODING": "ascii:strict", "PYTHONUTF8": "0"},
    )
    assert Process.returncode == 0, Process.stderr.decode("utf-8")
    Record = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Record["state"] == "completed" and Record["attempts"] == 1
    assert Record["reason"] == KReason and Record["result"] and Record["receipt"]


if __name__ == "__main__":
    print(
        EncodeJson(
            ObserveMode(FilePath(System.argv[1]), System.argv[2]), ensure_ascii=True
        )
    )
