from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from tests.Convert.Commands.BuildBadStep import BuildBadStep, KBadKinds
from tests.Convert.Commands.BuildExtraGeom import BuildExtraGeom
from tests.Convert.Commands.BuildSketchGeom import BuildSketchGeom
from tests.Convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Commands.WrapDocument import WrapDocument


# definitionless imported and unknown histories must fail conversion through the real cli process
@TestMark.parametrize("RecordKind", tuple(KBadKinds))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckBadStep(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildBadStep(RecordKind)
    assert Document.bodies and Document.feature_timeline
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


# a sketch reference alone must not qualify unrelated local body or mesh geometry
@TestMark.parametrize("RecordKind", ("Brep", "Mesh"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckSketchGeom(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildSketchGeom(RecordKind)
    assert Document.feature_timeline and not Document.bodies
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


# typed history must not hide unlinked geometry or substitute metadata for ownership
@TestMark.parametrize("RecordKind", ("UnlinkedBrep", "PlainMesh", "TaggedMesh"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckExtraGeom(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildExtraGeom(RecordKind)
    assert Document.bodies and Document.feature_timeline[-1].definition is not None
    if RecordKind == "UnlinkedBrep":
        assert Document.brep is not None
        assert all(not BodyValue.design_body_id for BodyValue in Document.brep.bodies)
    else:
        assert Document.meshes
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


# dimension driven sketch documents must preserve their qualified geometry without local solids
@TestMark.parametrize("IsNested", (False, True))
def CheckSketchOnly(IsNested: bool, TmpPath: FilePath) -> None:
    Document = MakeFusionDoc(
        DocumentSpec(
            "Typed sketch",
            "length",
            20.0,
            ProfileKind="rectangle",
            ConstrainRectangle=True,
        )
    )
    Document.AssertValid()
    if IsNested:
        Document = WrapDocument(Document)
        CheckJsonBlock(Document, "UnqualifiedAssembly", False, TmpPath)
        return
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "sketch.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Target.read_text(encoding="utf-8")) == LoadJson(Original)
    assert Source.read_text(encoding="utf-8") == Original
