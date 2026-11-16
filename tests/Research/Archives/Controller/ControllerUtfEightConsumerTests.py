from hashlib import sha256 as DigestBytes
from importlib.util import (
    module_from_spec as ModuleFromSpec,
    spec_from_file_location as SourceSpec,
)
from json import dumps as EncodeJson, loads as ParseJson
from locale import (
    LC_CTYPE as KCharLocale,
    getencoding as TextEncoding,
    setlocale as SetLocale,
)
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
import sys as System
from typing import Callable, cast as CastValue

from tests.Research.Archives.Controller.ControllerUtfEightTests import (
    InvokeApi,
    KReason,
    RefuseOutput,
    SeedClaim,
    WriteRecord,
)

# the archive gate must execute the same controller implementation as the committed checkout
KRepoRoot = FilePath(__file__).resolve().parents[4]


# the actual archive consumer must open artifact paths rather than observing decoded strings alone
def LoadGate(RootPath: FilePath) -> object:
    System.path.insert(0, str(KRepoRoot / "re/automation"))
    SpecValue = SourceSpec(
        "KitUtfEightArchiveGate", KRepoRoot / "re/automation/InferenceArchiveGate.py"
    )
    assert SpecValue is not None and SpecValue.loader is not None
    Module = ModuleFromSpec(SpecValue)
    SpecValue.loader.exec_module(Module)
    Construct = CastValue(Callable[[FilePath], object], Module.GateStore)
    return Construct(RootPath)


# a completed real lease must leave canonical artifacts readable through the existing archive consumer
def FinishGate(
    GateValue: object, Invoke: InvokeApi, RootPath: FilePath, ClaimPath: FilePath
) -> dict[str, object]:
    ResultPath = RootPath / "Result.json"
    Result: dict[str, object] = {"result": {"records": {"note": KReason}}}
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
    ReadResult = CastValue(
        Callable[[dict[str, object], dict[str, object]], object],
        getattr(GateValue, "result"),
    )
    assert ReadResult({"id": "utf-eight-job"}, {"utf-eight-job": JobValue}) == {
        "note": KReason
    }
    Artifact = Invoke("artifact", JobValue["result"])
    assert FilePath(CastValue(str, Artifact["path"])).read_bytes() == Expected
    return JobValue


# changing the consumer locale after startup keeps unicode filesystem arguments valid while exposing default text decoding
def ObserveGate(RootPath: FilePath) -> dict[str, object]:
    assert System.flags.utf8_mode == 0
    assert System.getfilesystemencoding().lower().replace("-", "") == "utf8"
    _ = SetLocale(KCharLocale, "C")
    Decoder = TextEncoding()
    if System.platform != "win32":
        assert Decoder.lower().replace("-", "") != "utf8"
    WorkRoot = RootPath / "Archive-\u00e9-e\u0301"
    WorkRoot.mkdir()
    GateValue = LoadGate(WorkRoot)
    Invoke = CastValue(InvokeApi, getattr(GateValue, "controller"))
    ClaimPath = SeedClaim(Invoke, WorkRoot)
    RefuseOutput(Invoke, WorkRoot, ClaimPath)
    JobValue = FinishGate(GateValue, Invoke, WorkRoot, ClaimPath)
    assert Invoke("events", "--after", "0")["next_after"] is None
    return {"decoder": Decoder, "job": JobValue}


# a real isolated consumer process must preserve unicode paths under a non utf eight default decoder
def CheckConsumer(TmpPath: FilePath) -> None:
    PlatformName = System.platform.lower()
    LocaleName = "en_US.UTF-8" if PlatformName == "darwin" else "C.UTF-8"
    ChildEnv = {**ProcessEnv, "PYTHONUTF8": "0", "PYTHONIOENCODING": "ascii:strict"}
    if PlatformName != "win32":
        ChildEnv["LC_ALL"] = LocaleName
    Process = RunProcess(
        [
            System.executable,
            "-B",
            "-m",
            "tests.Research.Archives.Controller.ControllerUtfEightConsumerTests",
            str(TmpPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        check=False,
        timeout=180,
        env=ChildEnv,
    )
    assert Process.returncode == 0, Process.stderr.decode("utf-8")
    assert Process.stderr == b""
    Record = CastValue(dict[str, object], ParseJson(Process.stdout))
    JobValue = CastValue(dict[str, object], Record["job"])
    assert JobValue["state"] == "completed" and JobValue["attempts"] == 1
    assert JobValue["reason"] == KReason and JobValue["result"] and JobValue["receipt"]
    if PlatformName != "win32":
        assert CastValue(str, Record["decoder"]).lower().replace("-", "") != "utf8"


if __name__ == "__main__":
    print(EncodeJson(ObserveGate(FilePath(System.argv[1])), ensure_ascii=True))
