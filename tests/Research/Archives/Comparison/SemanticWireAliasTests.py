from dataclasses import replace as ChangeRecord
from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Payloads.PayloadRoles import PayloadRole
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    ReadReport,
    RunComparison,
    WriteInputs,
)
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# independently sealing modified wire bytes keeps alias checks inside the real comparison process boundary
def SealFirstMut(Arguments: list[str], Record: dict[str, object]) -> None:
    FileName = FilePath(Arguments[Arguments.index("--first") + 1])
    Payload = EncodeJson(Record).encode()
    assert FileName.write_bytes(Payload) == len(Payload)
    Arguments[Arguments.index("--first-sha256") + 1] = DigestBytes(Payload).hexdigest()


# distinct incoming keys must never collapse contradictory or repeated observations into one decoded slot
@MarkValue.parametrize("FieldName", ("value", "id"))
@MarkValue.parametrize("AliasFirst", (False, True))
@MarkValue.parametrize("SameValue", (False, True))
def CheckCollisions(
    TmpPath: FilePath, FieldName: str, AliasFirst: bool, SameValue: bool
) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    FileName = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = ParseJson(FileName.read_text(encoding="utf-8"))
    Parameter = Record["parameters"]["$tuple"][0]
    Target = Parameter["value"] if FieldName == "value" else Parameter
    Original = Target[FieldName]
    Changed = (
        Original
        if SameValue
        else (Original + 1 if FieldName == "value" else Original + "-alias")
    )
    AliasName = FieldName.title()
    Replacement = (
        {AliasName: Changed, **Target} if AliasFirst else {**Target, AliasName: Changed}
    )
    Target.clear()
    Target.update(Replacement)
    SealFirstMut(Arguments, Record)
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout
    assert "colliding record field aliases" in Result.stderr
    assert not Result.stdout


# a single valid compatibility alias must retain its value without requiring canonical wire spelling
@MarkValue.parametrize("FieldName", ("value", "id"))
def CheckOneAlias(TmpPath: FilePath, FieldName: str) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    FileName = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = ParseJson(FileName.read_text(encoding="utf-8"))
    Parameter = Record["parameters"]["$tuple"][0]
    Target = Parameter["value"] if FieldName == "value" else Parameter
    Target[FieldName.title()] = Target.pop(FieldName)
    SealFirstMut(Arguments, Record)
    assert ReadReport(RunComparison(Arguments), "equal_observed_graph", 0)


# reflected legacy field metadata must not hide a collision on a canonical typed feature storage slot
def CheckTypedAlias(TmpPath: FilePath) -> None:
    Arguments = WriteInputs(TmpPath, MakeDocument(), MakeDocument())
    FileName = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = ParseJson(FileName.read_text(encoding="utf-8"))
    Target = Record["feature_timeline"]["$tuple"][1]["definition"]
    Target["AlongParameterId"] = Target["along_parameter_id"]
    SealFirstMut(Arguments, Record)
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout
    assert "colliding record field aliases" in Result.stderr
    assert not Result.stdout


# migration defaults must not overwrite an explicitly supplied payload role through a second alias
@MarkValue.parametrize("LegacyAlias", (False, True))
def CheckRoleClash(TmpPath: FilePath, LegacyAlias: bool) -> None:
    Content = b"independently authored evidence payload"
    Payload = BrepPayload(
        "evidence",
        "authored",
        "observation",
        "1",
        DigestBytes(Content).hexdigest(),
        Content,
        role=PayloadRole.KVerification,
    )
    Document = ChangeRecord(MakeDocument(), brep_payloads=(Payload,))
    Arguments = WriteInputs(TmpPath, Document, Document)
    FileName = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = ParseJson(FileName.read_text(encoding="utf-8"))
    Target = Record["brep_payloads"]["$tuple"][0]
    Target["Role"] = Target["role"]
    if LegacyAlias:
        del Target["role"]
    SealFirstMut(Arguments, Record)
    Result = RunComparison(Arguments)
    assert Result.returncode == 1, Result.stderr + Result.stdout
    assert "colliding" in Result.stderr
    assert not Result.stdout


# historical payloads missing migrated fields remain admissible when no incoming observation is overwritten
def CheckLegacyRead(TmpPath: FilePath) -> None:
    Content = b"independently authored legacy payload"
    Payload = BrepPayload(
        "legacy",
        "authored",
        "observation",
        "1",
        DigestBytes(Content).hexdigest(),
        Content,
    )
    Document = ChangeRecord(MakeDocument(), brep_payloads=(Payload,))
    Arguments = WriteInputs(TmpPath, Document, Document)
    FileName = FilePath(Arguments[Arguments.index("--first") + 1])
    Record = ParseJson(FileName.read_text(encoding="utf-8"))
    Target = Record["brep_payloads"]["$tuple"][0]
    del Target["role"]
    del Target["file_extension"]
    SealFirstMut(Arguments, Record)
    assert ReadReport(RunComparison(Arguments), "unresolved", 3)
