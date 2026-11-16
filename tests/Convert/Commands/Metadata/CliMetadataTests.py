from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Commands.Metadata.BuildMetadata import BuildMetadata, KMetadataCases
from tests.Convert.Commands.WrapDocument import WrapDocument


# root metadata must not smuggle retained native archives into user conversion output
@TestMark.parametrize("RecordKind", KMetadataCases)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckRetained(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildMetadata(RecordKind)
    assert Document.bodies and Document.feature_timeline[-1].definition is not None
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "RetainedMetadata", HasOutput, TmpPath)


# binary retention guards must traverse record attributes and provenance throughout nested documents
@TestMark.parametrize(
    "FieldName", ("Feature", "Sketch", "Assembly", "Provenance", "Source")
)
@TestMark.parametrize("RecordKind", ("Alias", "Nested", "Tuple", "NestedEmpty"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckFields(
    FieldName: str, RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildMetadata(RecordKind, FieldName)
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "RetainedMetadata", HasOutput, TmpPath)


# plain provenance hashes and text must survive conversion without losing the geometry contract
@TestMark.parametrize(
    "FieldName", ("Document", "Feature", "Sketch", "Assembly", "Provenance", "Source")
)
@TestMark.parametrize("IsNested", (False, True))
def CheckProvenance(FieldName: str, IsNested: bool, TmpPath: FilePath) -> None:
    Document = BuildMetadata("Provenance", FieldName)
    Document.AssertValid()
    if IsNested:
        Document = WrapDocument(Document)
    if IsNested or FieldName == "Assembly":
        CheckJsonBlock(Document, "UnqualifiedAssembly", False, TmpPath)
        return
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "provenance.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Target.read_text(encoding="utf-8")) == LoadJson(Original)
    assert Source.read_text(encoding="utf-8") == Original
