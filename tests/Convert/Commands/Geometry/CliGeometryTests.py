from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.Convert.Commands.Geometry.BuildStale import BuildStale
from tests.Convert.Commands.WrapDocument import WrapDocument


# a valid authoring contract must not conceal geometry that disagrees with its regenerated source
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckStaleBody(IsNested: bool, HasOutput: bool, TmpPath: FilePath) -> None:
    Document = BuildStale()
    assert "fusion.authoring" in Document.metadata
    Document.AssertValid()
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "UnqualifiedGeometry", HasOutput, TmpPath)
