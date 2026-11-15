from pathlib import Path as FilePath

from pytest import mark as TestMark

from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.Commands.Kind.BuildKinds import BuildKinds
from tests.convert.Commands.WrapDocument import WrapDocument


# opaque record kinds must refuse conversion without preventing inspection or replacing user output
@TestMark.parametrize(
    "RecordName,Variant",
    tuple(
        (RecordName, Variant)
        for RecordName in ("Mate", "MateEntity", "SketchEntity", "SketchRelation")
        for Variant in ("NativeEnum", "NativeText", "Unknown")
    )
    + (("Component", "Unknown"),),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckBadKinds(
    RecordName: str, Variant: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildKinds(RecordName, Variant)
    Document.AssertValid()
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "NativeRecord", HasOutput, TmpPath)


# canonical text and enum spellings must remain equivalent across qualified model conversion
@TestMark.parametrize(
    "RecordName", ("Component", "Mate", "MateEntity", "SketchEntity", "SketchRelation")
)
@TestMark.parametrize("Variant", ("KnownEnum", "KnownText"))
@TestMark.parametrize("IsNested", (False, True))
def CheckKnownKinds(
    RecordName: str, Variant: str, IsNested: bool, TmpPath: FilePath
) -> None:
    Document = BuildKinds(RecordName, Variant)
    if IsNested:
        Document = WrapDocument(Document)
    Document.AssertValid()
    if IsNested or RecordName in ("Component", "Mate", "MateEntity"):
        CheckJsonBlock(Document, "UnqualifiedAssembly", False, TmpPath)
        return
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "known.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert CadDocument.from_json(
        Target.read_text(encoding="utf-8")
    ) == CadDocument.from_json(Original)
    assert Source.read_text(encoding="utf-8") == Original
