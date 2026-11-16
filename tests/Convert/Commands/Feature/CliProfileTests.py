from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.Convert.Commands.Feature.BuildProfile import BuildProfile
from tests.Convert.Commands.Feature.ProfileCases import KProfileKinds
from tests.Convert.Commands.WrapDocument import WrapDocument


# profile tags must not replace finite nondegenerate closure evidence at the process boundary
@TestMark.parametrize("RecordKind", KProfileKinds)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckProfile(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildProfile(RecordKind)
    assert Document.bodies and Document.feature_timeline[-1].definition is not None
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)
