from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.Feature.BuildPlaneHist import BuildPlaneHist
from tests.convert.Commands.WrapDocument import WrapDocument


# cached planes need active qualified history before the cli can publish model output
@TestMark.parametrize("RecordKind", ("Global", "ConfigState", "ConfigRecord", "Active"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckPlaneHist(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildPlaneHist(RecordKind)
    assert Document.support_planes and Document.feature_timeline
    assert not Document.bodies and not Document.sketches and Document.brep is None
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(
        Document,
        "UnqualifiedGeometry" if RecordKind == "Active" else "IncompleteFeature",
        HasOutput,
        TmpPath,
    )
