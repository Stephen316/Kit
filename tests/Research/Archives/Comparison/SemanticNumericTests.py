from dataclasses import replace as ChangeRecord
from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    KTolerances,
    ReadReport,
    RunComparison,
    WriteInputs,
)
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# independently owned numeric controls expose precision loss without changing the geometric fixture grammar
def WithNumber(
    Document: CadDocument, Number: int | float, KindName: ValueKind, UnitName: str
) -> CadDocument:
    BossStep = Document.feature_timeline[1]
    Numeric = Parameter(
        "authorednumber",
        "authored numeric control",
        ParameterValue(Number, KindName, UnitName),
        owner_id=BossStep.id,
    )
    return ChangeRecord(
        Document,
        parameters=Document.parameters + (Numeric,),
        feature_timeline=(
            Document.feature_timeline[0],
            ChangeRecord(
                BossStep, parameter_ids=BossStep.parameter_ids + (Numeric.id,)
            ),
        ),
    )


# integer magnitudes above floating precision must remain distinguishable after quantity normalization
@MarkValue.parametrize(
    "KindName,UnitName", ((ValueKind.KNumber, ""), (ValueKind.KLength, "mm"))
)
def CheckHugeNumber(TmpPath: FilePath, KindName: ValueKind, UnitName: str) -> None:
    First = WithNumber(MakeDocument(), 2**53, KindName, UnitName)
    Second = WithNumber(MakeDocument(), 2**53 + 1, KindName, UnitName)
    Arguments = WriteInputs(TmpPath, First, Second)
    TolerancePath = FilePath(Arguments[Arguments.index("--tolerances") + 1])
    Payload = EncodeJson(dict.fromkeys(KTolerances, 0), sort_keys=True).encode()
    assert TolerancePath.write_bytes(Payload) == len(Payload)
    Arguments[Arguments.index("--tolerances-sha256") + 1] = DigestBytes(
        Payload
    ).hexdigest()
    assert ReadReport(RunComparison(Arguments), "different", 2)["comparison"]


# dimensionless integer controls retain exact distinctions even when floating tolerances are permissive
def CheckCountExact(TmpPath: FilePath) -> None:
    First = WithNumber(MakeDocument(), 100, ValueKind.KNumber, "")
    Second = WithNumber(MakeDocument(), 101, ValueKind.KNumber, "")
    Arguments = WriteInputs(TmpPath, First, Second)
    TolerancePath = FilePath(Arguments[Arguments.index("--tolerances") + 1])
    Payload = EncodeJson({**KTolerances, "dimensionless": 1}, sort_keys=True).encode()
    assert TolerancePath.write_bytes(Payload) == len(Payload)
    Arguments[Arguments.index("--tolerances-sha256") + 1] = DigestBytes(
        Payload
    ).hexdigest()
    assert ReadReport(RunComparison(Arguments), "different", 2)["comparison"]


# exact scaling arithmetic must retain declared floating tolerance across small physical unit conversions
def CheckSmallUnits(TmpPath: FilePath) -> None:
    First = WithNumber(MakeDocument(), 0.1, ValueKind.KLength, "mm")
    Second = WithNumber(MakeDocument("inch", "in"), 0.1 / 25.4, ValueKind.KLength, "in")
    Arguments = WriteInputs(TmpPath, First, Second)
    Arguments[Arguments.index("--second-geometry-unit") + 1] = "in"
    assert ReadReport(RunComparison(Arguments), "equal_observed_graph", 0)["comparison"]


# legitimate retained metadata stays unresolved within the raw json depth budget and refuses beyond it
@MarkValue.parametrize("DepthValue", (52, 65))
def CheckJsonDepth(TmpPath: FilePath, DepthValue: int) -> None:
    Metadata: dict[str, object] = {"authored_leaf": "retained observation"}
    for LevelIndex in range(DepthValue):
        Metadata = {f"authored_level_{LevelIndex}": Metadata}
    Document = ChangeRecord(MakeDocument(), metadata=Metadata)
    Result = RunComparison(WriteInputs(TmpPath, Document, Document))
    if DepthValue > 64:
        assert Result.returncode == 1, Result.stderr + Result.stdout
        assert Result.stdout == ""
        assert "structural limit" in Result.stderr
        return
    assert ReadReport(Result, "unresolved", 3)["sources"]
