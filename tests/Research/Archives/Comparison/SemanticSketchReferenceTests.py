from dataclasses import replace as ChangeRecord
from hashlib import sha256 as DigestBytes
from importlib.util import (
    module_from_spec as ModuleFromSpec,
    spec_from_file_location as SourceSpec,
)
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
import sys as System
from types import ModuleType
from typing import Callable, cast as CastValue

from pytest import mark as MarkValue

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.serialization.EncodeData import ToData
from tests.Research.Archives.Comparison.NeutralReaderRunnerTests import (
    PrepareReaders,
    ReadArtifact,
)
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    ReadReport,
    RunComparison,
    WriteInputs,
)
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument
from tests.Research.SupervisorClient import FixtureJob

# pinned process fixtures must execute the implementation from the checkout that owns these tests
KRepoRoot = FilePath(__file__).resolve().parents[4]


# inventory checks need the real evidence component without changing project import search paths
def LoadEvidence() -> ModuleType:
    SpecValue = SourceSpec(
        "KitReaderEvidence", KRepoRoot / "re/automation/ReaderEvidence.py"
    )
    if SpecValue is None or SpecValue.loader is None:
        raise ImportError("reader evidence source is unavailable")
    Module = ModuleFromSpec(SpecValue)
    SpecValue.loader.exec_module(Module)
    return Module


# the typed boundary preserves the original evidence implementation instead of copying its traversal
KReadEvidence = CastValue(
    Callable[[object], dict[str, object]], LoadEvidence().reader_evidence
)


# authored sketch history reproduces the actual native representation without relying on captured identities
def ReferenceInput(TmpPath: FilePath) -> list[str]:
    Document = MakeDocument()
    SketchStep = ChangeRecord(
        Document.feature_timeline[0], definition=None, sketch_id=Document.sketches[0].id
    )
    Document = ChangeRecord(
        Document, feature_timeline=(SketchStep, Document.feature_timeline[1])
    )
    return WriteInputs(TmpPath, Document, Document)


# malformed wire variants isolate the boundary that could otherwise mistake metadata for declared sketch history
def ChangeWire(Record: dict[str, object], ModeName: str) -> dict[str, object]:
    WireValue = ParseJson(EncodeJson(Record))
    StepValue = WireValue["feature_timeline"]["$tuple"][0]
    if ModeName == "operation":
        StepValue["operation"] = ToData(BooleanOp.KCreate)
    elif ModeName == "non-reference":
        StepValue["kind"] = ToData(FeatureKind.KExtrusion)
    elif ModeName == "unknown":
        StepValue["kind"] = "authored_unknown_kind"
    elif ModeName == "no-target":
        StepValue["sketch_id"] = None
    elif ModeName == "dangling":
        StepValue["sketch_id"] = "missing"
    elif ModeName == "duplicate":
        WireValue["sketches"]["$tuple"].append(
            ParseJson(EncodeJson(WireValue["sketches"]["$tuple"][0]))
        )
    elif ModeName == "nested-sketch":
        WireValue["metadata"]["fake_sketch"] = WireValue["sketches"]["$tuple"].pop()
    elif ModeName == "nested-step":
        WireValue["metadata"]["fake_step"] = ParseJson(EncodeJson(StepValue))
    elif ModeName == "root":
        WireValue["$type"] = "UnrecognizedRoot"
    elif ModeName == "source":
        WireValue["source"] = {}
    elif ModeName == "tuple":
        WireValue["sketches"] = WireValue["sketches"]["$tuple"]
    elif ModeName == "raw-kind":
        StepValue["kind"] = "reference"
    elif ModeName != "valid":
        raise ValueError("unknown reference fixture mode")
    return CastValue(dict[str, object], WireValue)


# independent seals ensure both diagnostic components consume the same modified byte observations
def SealSketchMut(Arguments: list[str], ModeName: str) -> FilePath:
    FirstPath = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = ChangeWire(ParseJson(FirstPath.read_text(encoding="utf-8")), ModeName)
    Payload = EncodeJson(Record).encode()
    for SideName in ("first", "second"):
        InputPath = FilePath(Arguments[Arguments.index(f"--{SideName}") + 1])
        assert InputPath.write_bytes(Payload) == len(Payload)
        Arguments[Arguments.index(f"--{SideName}-sha256") + 1] = DigestBytes(
            Payload
        ).hexdigest()
    return FirstPath


# the evidence inventory must run in a real process against an immutable input file
def InventoryRun(InputPath: FilePath, ExitCode: int = 0) -> dict[str, object]:
    Process = RunProcess(
        [
            System.executable,
            "-B",
            "-m",
            "tests.Research.Archives.Comparison.SemanticSketchReferenceTests",
            str(InputPath),
            DigestBytes(InputPath.read_bytes()).hexdigest(),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == ExitCode, Process.stderr + Process.stdout
    return (
        CastValue(dict[str, object], ParseJson(Process.stdout))
        if ExitCode == 0
        else {"error": Process.stderr}
    )


# valid declared sketch references preserve typed history and its consuming operation dependency
@MarkValue.parametrize("ModeName", ("valid", "raw-kind"))
def CheckReference(TmpPath: FilePath, ModeName: str) -> None:
    Arguments = ReferenceInput(TmpPath)
    InputPath = SealSketchMut(Arguments, ModeName)
    Report = ReadReport(RunComparison(Arguments), "equal_observed_graph", 0)
    Sources = ParseJson(EncodeJson(Report["sources"]))
    assert any(
        Value.get("classification") == "declared_sketch_reference"
        for Value in Sources["left"]["observations"]
    )
    Inventory = ParseJson(EncodeJson(InventoryRun(InputPath)))
    assert not any(
        Value["reason"] == "missing_feature_definition"
        for Value in Inventory["unresolved"]
    )
    assert Inventory["portable_complete"] is False
    assert Inventory["native_acceptance"] == "not_established"


# operation bearing unknown dangling duplicate and nested records must keep their definition diagnostics
@MarkValue.parametrize(
    "ModeName",
    (
        "operation",
        "non-reference",
        "unknown",
        "no-target",
        "dangling",
        "duplicate",
        "nested-sketch",
        "nested-step",
        "root",
        "source",
        "tuple",
    ),
)
def CheckUnresolved(TmpPath: FilePath, ModeName: str) -> None:
    Arguments = ReferenceInput(TmpPath)
    InputPath = SealSketchMut(Arguments, ModeName)
    Inventory = ParseJson(EncodeJson(InventoryRun(InputPath)))
    Missing = [
        Value
        for Value in Inventory["unresolved"]
        if Value["reason"] == "missing_feature_definition"
    ]
    assert Missing
    if ModeName == "nested-step":
        assert any(Value["path"].startswith("/metadata/") for Value in Missing)
    Result = RunComparison(Arguments)
    assert Result.returncode in (1, 3), Result.stderr + Result.stdout


# a real native worker must classify the declared sketch reference while retaining unrelated source issues
def CheckNativePart(TmpPath: FilePath) -> None:
    Harness = PrepareReaders(TmpPath)
    SourcePath = (
        KRepoRoot
        / "re/automation/PairedCaptures/P03/fusion-8d53584027ff/P03-fusion-baseline-a.f3d"
    )
    Harness.BindBytes("p03-native", SourcePath.read_bytes())
    Harness.SubmitJobs(
        [
            FixtureJob(
                "p03-reader",
                "reader.neutral",
                inputs={"source": "p03-native"},
                options={
                    "scope": "p03-reference-observation",
                    "source_format": "fusion.f3d",
                    "strict": True,
                    "configuration": None,
                },
                max_attempts=1,
                lease_seconds=30,
            )
        ]
    )
    _ = Harness.RunIdle(MaxSeconds=120)
    JobInfo = Harness.ReadJob("p03-reader")
    assert JobInfo["state"] == "completed", JobInfo
    Stored = ParseJson(EncodeJson(Harness.ReadResult("p03-reader")))
    Evidence = ParseJson(
        ReadArtifact(Harness, Stored["output_artifacts"]["reader-evidence"])
    )
    assert not any(
        Value["reason"] == "missing_feature_definition"
        and Value["path"] == "/feature_timeline/$tuple/0/definition"
        for Value in Evidence["unresolved"]
    )
    assert Evidence["unresolved"] and Evidence["portable_complete"] is False
    assert Stored["result"]["records"]["semantic_qualification"] == "unverified"


# oversized root inventories remain subject to the unchanged bounded evidence visitor
def CheckRootCap(TmpPath: FilePath) -> None:
    Arguments = ReferenceInput(TmpPath)
    InputPath = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = ParseJson(InputPath.read_text(encoding="utf-8"))
    Record["sketches"] = {"$tuple": [None] * 200001}
    _ = InputPath.write_text(EncodeJson(Record), encoding="utf-8")
    Report = InventoryRun(InputPath, ExitCode=1)
    assert "reader evidence exceeds 200000 entries" in str(Report["error"])


# sealed child process intake keeps inventory observations independent from fixture memory
def MainInventory() -> None:
    InputPath = FilePath(System.argv[1])
    with InputPath.open("rb") as SourceFile:
        Content = SourceFile.read(32 * 1024 * 1024 + 1)
    if (
        len(Content) > 32 * 1024 * 1024
        or DigestBytes(Content).hexdigest() != System.argv[2]
    ):
        raise ValueError("inventory fixture input differs from its bounded byte seal")
    print(EncodeJson(KReadEvidence(ParseJson(Content))))


if __name__ == "__main__":
    MainInventory()
