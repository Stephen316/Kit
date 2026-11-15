from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.Sketch.BuildInactive import BuildInactive
from tests.convert.Commands.Sketch.BuildSketches import BuildSketches
from tests.convert.Commands.WrapDocument import WrapDocument


# history refusal must preserve user files while keeping incomplete sketches available for inspection
@TestMark.parametrize(
    "RecordKind",
    (
        "Empty",
        "Unrelated",
        "Partial",
        "Global",
        "ConfigState",
        "ConfigRecord",
        "Dependency",
        "SketchSuppressed",
    ),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckSketchHist(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = (
        BuildSketches(RecordKind)
        if RecordKind in ("Empty", "Unrelated", "Partial")
        else BuildInactive(RecordKind)
    )
    assert Document.parameters and Document.sketches
    assert not Document.bodies and Document.brep is None
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(
        Document,
        "MissingFeatureHistory" if RecordKind == "Empty" else "IncompleteFeature",
        HasOutput,
        TmpPath,
    )
