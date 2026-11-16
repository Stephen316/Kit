from dataclasses import replace as ChangeRecord
from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    ReadReport,
    RunComparison,
    WriteInputs,
)
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# independent primitive controls expose malformed domains without changing the authored geometric fixture
def WithPrimitive(KindName: ValueKind, Value: str | int | float | bool) -> CadDocument:
    Document = MakeDocument()
    BossStep = Document.feature_timeline[1]
    ParamValue = Parameter(
        "primitive",
        "authored primitive",
        ParameterValue(Value, KindName),
        owner_id=BossStep.id,
    )
    return ChangeRecord(
        Document,
        parameters=Document.parameters + (ParamValue,),
        feature_timeline=(
            Document.feature_timeline[0],
            ChangeRecord(
                BossStep, parameter_ids=BossStep.parameter_ids + (ParamValue.id,)
            ),
        ),
    )


# repeated malformed observations must remain unresolved rather than manufacture equality on both sides
@MarkValue.parametrize(
    "KindName,Value",
    (
        (ValueKind.KNumber, True),
        (ValueKind.KNumber, "eleven"),
        (ValueKind.KInteger, True),
        (ValueKind.KInteger, 7.5),
        (ValueKind.KBoolean, 1),
        (ValueKind.KBoolean, "true"),
        (ValueKind.KString, 7),
        (ValueKind.KString, False),
    ),
)
def CheckWrongValue(
    TmpPath: FilePath, KindName: ValueKind, Value: str | int | float | bool
) -> None:
    Document = WithPrimitive(KindName, Value)
    Report = ReadReport(
        RunComparison(WriteInputs(TmpPath, Document, Document)), "unresolved", 3
    )
    Sources = ParseJson(EncodeJson(Report["sources"]))
    for SideName in ("left", "right"):
        Issues = [
            IssueValue
            for IssueValue in Sources[SideName]["unresolved"]
            if IssueValue["reason"] == "invalid_parameter_value_domain"
        ]
        assert len(Issues) == 1
        assert Issues[0]["observation"] == {
            "declared_kind": KindName.value,
            "value": Value,
            "value_type": type(Value).__name__,
            "unit": "",
        }
        assert len(Issues[0]["evidence_sha256"]) == 64


# valid primitive values and enum aliases keep their intended exact or quantity specific comparison policy
@MarkValue.parametrize(
    "KindName,Value",
    (
        (ValueKind.KNumber, 11),
        (ValueKind.NUMBER, 11.5),
        (ValueKind.KInteger, 7),
        (ValueKind.INTEGER, -3),
        (ValueKind.KBoolean, True),
        (ValueKind.BOOLEAN, False),
        (ValueKind.KString, "authored text"),
        (ValueKind.STRING, ""),
    ),
)
def CheckValidValue(
    TmpPath: FilePath, KindName: ValueKind, Value: str | int | float | bool
) -> None:
    Document = WithPrimitive(KindName, Value)
    Report = ReadReport(
        RunComparison(WriteInputs(TmpPath, Document, Document)),
        "equal_observed_graph",
        0,
    )
    assert Report["semantic_qualification"] == "unverified"


# unsupported kinds stay visible as unresolved observations instead of acquiring invented primitive semantics
def CheckUnknownTag(TmpPath: FilePath) -> None:
    Document = WithPrimitive(ValueKind.KString, "observed text")
    Arguments = WriteInputs(TmpPath, Document, Document)
    for SideName in ("first", "second"):
        InputPath = FilePath(Arguments[Arguments.index(f"--{SideName}") + 1])
        Record = ParseJson(InputPath.read_text(encoding="utf-8"))
        Record["parameters"]["$tuple"][-1]["value"]["kind"] = "authored_unknown_kind"
        Payload = EncodeJson(Record).encode()
        assert InputPath.write_bytes(Payload) == len(Payload)
        Arguments[Arguments.index(f"--{SideName}-sha256") + 1] = DigestBytes(
            Payload
        ).hexdigest()
    Report = ReadReport(RunComparison(Arguments), "unresolved", 3)
    Sources = ParseJson(EncodeJson(Report["sources"]))
    assert any(
        IssueValue["reason"] == "unsupported_parameter_value_kind"
        for IssueValue in Sources["left"]["unresolved"]
    )
