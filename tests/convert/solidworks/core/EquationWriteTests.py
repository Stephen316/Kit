from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert import convert as ConvertFile
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.solidworks.core.EquationTarget import KUnresolvedEqTargets
from tests.convert.api.ApiTestPaths import KRootPath, KSamplePath


def TestBoundWrite(TmpPath: FilePath) -> None:
    SourcePath = (
        KRootPath
        / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
        / "P04-solidworks-baseline-a.SLDPRT"
    )
    Document = OpenDocument(SourcePath)
    Parameters = {Parameter.id: Parameter for Parameter in Document.parameters}
    for TargetName, SourceNames in (
        ("cut_left_mm", ("width_mm", "cut_width_mm")),
        ("cut_bottom_mm", ("height_mm", "cut_height_mm")),
    ):
        Target = next(
            Value for Value in Document.parameters if Value.name == TargetName
        )
        assert Target.expression is not None
        assert Target.expression.language == "solidworks"
        assert Target.expression.source.replace(" ", "") == (
            f'("{SourceNames[0]}@RectangleSketch"-"{SourceNames[1]}@CutSketch")/2'
        )
        assert (
            tuple(
                Parameters[ParamId].name for ParamId in Target.expression.parameter_ids
            )
            == SourceNames
        )
        assert not Target.attributes.get("unresolved_equation_references")
    assert not Document.metadata.get(KUnresolvedEqTargets)
    NeutralPath = TmpPath / "Neutral.json"
    _ = NeutralPath.write_bytes(b"existing destination")
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = WriteDocument(Document, NeutralPath, overwrite=True)
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = ConvertFile(SourcePath, NeutralPath, overwrite=True)
    assert NeutralPath.read_bytes() == b"existing destination"


@TestMark.parametrize("RelabelSource", (False, True))
def TestMissingLink(TmpPath: FilePath, RelabelSource: bool) -> None:
    Original = OpenDocument(KSamplePath)
    if RelabelSource:
        Original = ReplaceData(
            Original, source=ReplaceData(Original.source, format_id="interchange.json")
        )
    Parameter, *Remaining = Original.parameters
    Marked = ReplaceData(
        Parameter,
        attributes={
            **Parameter.attributes,
            "unresolved_equation_references": ("MissingDimension@Sketch1",),
        },
    )
    Document = ReplaceData(Original, parameters=(Marked, *Remaining))
    SourcePath = TmpPath / "Research.json"
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing destination")
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    assert OpenDocument(SourcePath) == Document
    with RaisesError(ValueError, match="unresolved SOLIDWORKS equation references"):
        _ = WriteDocument(Document, TargetPath, overwrite=True)
    with RaisesError(ValueError, match="MissingDimension@Sketch1"):
        _ = ConvertFile(SourcePath, TargetPath, overwrite=True)
    assert TargetPath.read_bytes() == b"existing destination"


@TestMark.parametrize("RelabelSource", (False, True))
def TestBadTarget(TmpPath: FilePath, RelabelSource: bool) -> None:
    Original = OpenDocument(KSamplePath)
    if RelabelSource:
        Original = ReplaceData(
            Original, source=ReplaceData(Original.source, format_id="interchange.json")
        )
    Document = ReplaceData(
        Original,
        metadata={
            **Original.metadata,
            KUnresolvedEqTargets: (
                {"lhs": "MissingDimension@Sketch1", "reason": "unresolved_target"},
            ),
        },
    )
    SourcePath = TmpPath / "Research.json"
    TargetPath = TmpPath / "Target.json"
    _ = SourcePath.write_text(Document.to_json(), encoding="utf-8")
    with RaisesError(ValueError, match="unresolved_target"):
        _ = ConvertFile(SourcePath, TargetPath)
    assert not TargetPath.exists()
