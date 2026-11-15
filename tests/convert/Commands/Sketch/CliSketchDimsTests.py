from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.Sketch.BuildSketchDims import BuildSketchDims
from tests.convert.Commands.WrapDocument import WrapDocument


# sketch references must not qualify literal stale or nondriving geometry for conversion
@TestMark.parametrize(
    "RecordKind",
    (
        "Circle",
        "Rectangle",
        "Cylinder",
        "Cuboid",
        "NoContract",
        "Stale",
        "Suppressed",
        "Reference",
    ),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckSketchDims(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildSketchDims(RecordKind)
    assert Document.feature_timeline
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "UnqualifiedGeometry", HasOutput, TmpPath)
