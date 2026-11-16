from dataclasses import replace as ChangeRecord
from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

from pytest import mark as MarkValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.serialization.JsonCodec import DumpJson, LoadJson
from tests.Research.Archives.Comparison.SemanticDocuments import (
    ChangeSemantic,
    MakeDocument,
    MakeSymmetric,
    MakeUnresolved,
    PermuteModel,
)

# the subprocess must execute the implementation from the same committed checkout as these fixtures
KRepoRoot = FilePath(__file__).resolve().parents[4]

# physical tolerances remain independently sealed and explicit for every comparison process
KTolerances = {
    "length_mm": 1e-8,
    "angle_rad": 1e-10,
    "dimensionless": 1e-10,
    "area_mm2": 1e-8,
    "volume_mm3": 1e-8,
}


# fixture serialization passes through the real codec and document validators before invoking the cli
def WriteDocument(FileName: FilePath, Document: CadDocument) -> None:
    AssertValid(Document)
    TextValue = DumpJson(Document)
    Decoded = LoadJson(TextValue)
    assert isinstance(Decoded, CadDocument)
    AssertValid(Decoded)
    assert Decoded == Document
    assert FileName.write_text(TextValue, encoding="utf-8") == len(TextValue)


# each invocation consumes separately written typed inputs rather than in memory matcher substitutes
def WriteInputs(
    TmpPath: FilePath, First: CadDocument, Second: CadDocument
) -> list[str]:
    FirstPath = TmpPath / "First.json"
    SecondPath = TmpPath / "Second.json"
    TolerancePath = TmpPath / "Tolerances.json"
    WriteDocument(FirstPath, First)
    WriteDocument(SecondPath, Second)
    TextValue = EncodeJson(KTolerances, sort_keys=True)
    assert TolerancePath.write_text(TextValue, encoding="utf-8") == len(TextValue)
    return [
        "--first",
        str(FirstPath),
        "--first-sha256",
        DigestBytes(FirstPath.read_bytes()).hexdigest(),
        "--first-geometry-unit",
        "mm",
        "--second",
        str(SecondPath),
        "--second-sha256",
        DigestBytes(SecondPath.read_bytes()).hexdigest(),
        "--second-geometry-unit",
        "mm",
        "--tolerances",
        str(TolerancePath),
        "--tolerances-sha256",
        DigestBytes(TolerancePath.read_bytes()).hexdigest(),
    ]


# immutable input snapshots detect accidental rewriting at the public process boundary
def RunComparison(Arguments: list[str]) -> CompletedProcess[str]:
    Inputs = tuple(
        FilePath(Arguments[Arguments.index(FlagName) + 1])
        for FlagName in ("--first", "--second", "--tolerances")
    )
    Original = tuple(InputPath.read_bytes() for InputPath in Inputs)
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/SemanticComparison.py"),
            *Arguments,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert tuple(InputPath.read_bytes() for InputPath in Inputs) == Original
    return Result


# every valid report must retain honest research scope regardless of comparison outcome
def ReadReport(
    Result: CompletedProcess[str], Expected: str, ExitCode: int
) -> dict[str, object]:
    assert Result.returncode == ExitCode, Result.stderr + Result.stdout
    Report = CastValue(dict[str, object], ParseJson(Result.stdout))
    assert Report["comparison_version"] == 1
    assert Report["status"] == Expected
    assert Report["semantic_qualification"] == "unverified"
    assert Report["independent_source_inventory"] == "not_supplied"
    assert Report["native_acceptance"] == "not_established"
    assert isinstance(Report["input_sha256"], dict)
    return Report


# renaming and collection order must not manufacture differences in an editable rectangle and boss
def CheckReidentify(TmpPath: FilePath) -> None:
    Arguments = WriteInputs(
        TmpPath, MakeDocument(), PermuteModel(MakeDocument("renamed"))
    )
    Report = ReadReport(RunComparison(Arguments), "equal_observed_graph", 0)
    assert Report["input_sha256"] == {
        "left": Arguments[Arguments.index("--first-sha256") + 1],
        "right": Arguments[Arguments.index("--second-sha256") + 1],
        "tolerances": Arguments[Arguments.index("--tolerances-sha256") + 1],
    }
    Comparison = CastValue(dict[str, object], Report["comparison"])
    assert Comparison["matches"]
    for FieldName in (
        "ambiguous",
        "unmatched_left",
        "unmatched_right",
        "reference_differences",
    ):
        assert not Comparison[FieldName]
    assert Comparison["search_limited"] is False


# explicit inch coordinates and owned inch dimensions must compare in the same physical unit system
def CheckUnitScale(TmpPath: FilePath) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument("inch", "in"))
    Arguments[Arguments.index("--second-geometry-unit") + 1] = "in"
    assert ReadReport(RunComparison(Arguments), "equal_observed_graph", 0)["comparison"]


# equivalent scalar literals with changed dependencies still represent different parametric design intent
@MarkValue.parametrize(
    "ChangeName",
    ("role", "expression", "expression_dependency", "dependency", "relation"),
)
def CheckDesignDiff(TmpPath: FilePath, ChangeName: str) -> None:
    Original = MakeDocument()
    First = (
        ChangeSemantic(Original, "expression")
        if ChangeName == "expression_dependency"
        else Original
    )
    Arguments = WriteInputs(TmpPath, First, ChangeSemantic(Original, ChangeName))
    assert ReadReport(RunComparison(Arguments), "different", 2)["comparison"]


# changed coordinates must be visible even when every scalar parameter and history record is unchanged
def CheckShapeDiff(TmpPath: FilePath) -> None:
    Original = MakeDocument()
    Profile = Original.sketches[0]
    Entity = ChangeRecord(
        Profile.entities[0],
        geometry=LineGeometry(PlaneVector(0.0, 0.0), PlaneVector(41.0, 0.0)),
    )
    Changed = ChangeRecord(
        Original,
        sketches=(ChangeRecord(Profile, entities=(Entity,) + Profile.entities[1:]),),
    )
    assert ReadReport(
        RunComparison(WriteInputs(TmpPath, Original, Changed)), "different", 2
    )["comparison"]


# symmetric duplicate geometry must preserve ambiguity instead of selecting arbitrary entity identities
def CheckSymmetry(TmpPath: FilePath) -> None:
    Document = MakeSymmetric()
    Report = ReadReport(
        RunComparison(WriteInputs(TmpPath, Document, Document)), "ambiguous", 3
    )
    assert CastValue(dict[str, object], Report["comparison"])["ambiguous"]


# the bounded search contract must report exhaustion without treating an unfinished search as equality
def CheckSearchCap(TmpPath: FilePath) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument("renamed"))
    Report = ReadReport(
        RunComparison(Arguments + ["--max-candidates", "1"]), "incomplete", 3
    )
    assert CastValue(dict[str, object], Report["comparison"])["search_limited"] is True


# identical retained bytes and unsupported model domains cannot establish semantic equivalence
@MarkValue.parametrize(
    "DomainName",
    (
        "metadata",
        "native",
        "mesh",
        "brep",
        "assembly",
        "source_attributes",
        "provenance_attributes",
        "confidence",
    ),
)
def CheckUnresolved(TmpPath: FilePath, DomainName: str) -> None:
    Document = MakeUnresolved(DomainName)
    Report = ReadReport(
        RunComparison(WriteInputs(TmpPath, Document, Document)), "unresolved", 3
    )
    Sources = CastValue(dict[str, dict[str, object]], Report["sources"])
    assert Sources["left"]["unresolved"]
    assert Sources["right"]["unresolved"]


# independent byte seals reject changes to any comparison input before graph interpretation begins
@MarkValue.parametrize(
    "FlagName", ("--first-sha256", "--second-sha256", "--tolerances-sha256")
)
def CheckInputPins(TmpPath: FilePath, FlagName: str) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    Arguments[Arguments.index(FlagName) + 1] = "f" * 64
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout


# malformed json and nonfinite numbers must be refused despite valid independent seals over their bytes
@MarkValue.parametrize(
    "Payload",
    (
        b"{",
        b'{"$type":"CadDocument","$type":"CadDocument"}',
        b'{"number":NaN}',
        b'{"number":Infinity}',
        b"[]",
    ),
)
def CheckBadDoc(TmpPath: FilePath, Payload: bytes) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    FirstPath = FilePath(Arguments[Arguments.index("--first") + 1])
    assert FirstPath.write_bytes(Payload) == len(Payload)
    Arguments[Arguments.index("--first-sha256") + 1] = DigestBytes(Payload).hexdigest()
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout


# duplicate keys in otherwise valid documents must fail before permissive decoding can erase evidence
def CheckRepeatKey(TmpPath: FilePath) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    FirstPath = FilePath(Arguments[Arguments.index("--first") + 1])
    TextValue = FirstPath.read_text(encoding="utf-8")
    Record = CastValue(dict[str, object], ParseJson(TextValue))
    Payload = ('{"$type":' + EncodeJson(Record["$type"]) + "," + TextValue[1:]).encode()
    assert FirstPath.write_bytes(Payload) == len(Payload)
    Arguments[Arguments.index("--first-sha256") + 1] = DigestBytes(Payload).hexdigest()
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout


# nonfinite data inside an otherwise valid typed root cannot become an unresolved equality claim
def CheckNonfinite(TmpPath: FilePath) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    FirstPath = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = CastValue(
        dict[str, object], ParseJson(FirstPath.read_text(encoding="utf-8"))
    )
    Record["metadata"] = {"authored_number": float("nan")}
    Payload = EncodeJson(Record).encode()
    assert FirstPath.write_bytes(Payload) == len(Payload)
    Arguments[Arguments.index("--first-sha256") + 1] = DigestBytes(Payload).hexdigest()
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout


# tolerance objects reject omitted unknown repeated negative boolean and nonfinite values at process intake
@MarkValue.parametrize(
    "Payload",
    (
        b"{}",
        ('{"length_mm":0,' + EncodeJson(KTolerances)[1:]).encode(),
        EncodeJson({**KTolerances, "extra": 0}).encode(),
        EncodeJson({**KTolerances, "length_mm": -1}).encode(),
        EncodeJson({**KTolerances, "angle_rad": True}).encode(),
        EncodeJson({**KTolerances, "dimensionless": float("inf")}).encode(),
    ),
)
def CheckBadBounds(TmpPath: FilePath, Payload: bytes) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    TolerancePath = FilePath(Arguments[Arguments.index("--tolerances") + 1])
    assert TolerancePath.write_bytes(Payload) == len(Payload)
    Arguments[Arguments.index("--tolerances-sha256") + 1] = DigestBytes(
        Payload
    ).hexdigest()
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout


# symlink aliases must not bypass the regular sealed input contract for documents or tolerances
@MarkValue.parametrize("FlagName", ("--first", "--second", "--tolerances"))
def CheckLinkInputs(TmpPath: FilePath, FlagName: str) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    AliasPath = TmpPath / "Alias.json"
    AliasPath.symlink_to(FilePath(Arguments[Arguments.index(FlagName) + 1]))
    Arguments[Arguments.index(FlagName) + 1] = str(AliasPath)
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout


# candidate budgets outside the declared range must fail intake before any semantic claim is produced
@MarkValue.parametrize("BudgetText", ("0", "100001", "nan"))
def CheckBadBudget(TmpPath: FilePath, BudgetText: str) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    Result = RunComparison(Arguments + ["--max-candidates", BudgetText])
    assert Result.returncode == 1, Result.stderr + Result.stdout
