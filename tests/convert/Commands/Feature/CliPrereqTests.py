from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.Feature.BuildCreator import BuildCreator, KCreatorCases
from tests.convert.Commands.Feature.BuildModifier import BuildModifier
from tests.convert.Commands.Feature.ModifierCases import KModifierCases
from tests.convert.Commands.WrapDocument import WrapDocument


# typed definitions must not qualify generators whose creation or operand prerequisites are missing
@TestMark.parametrize("RecordKind", (*KModifierCases, *KCreatorCases))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckPrereqs(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = (
        BuildModifier(RecordKind)
        if RecordKind in KModifierCases
        else BuildCreator(RecordKind)
    )
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


# distinct active operands alone must not qualify generic boolean geometry without regeneration evidence
@TestMark.parametrize("RecordKind", ("CombineValid", "CombineCut"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckTwoInputs(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildModifier(RecordKind)
    Document.AssertValid()
    assert len(set(Document.feature_timeline[-1].input_feature_ids)) == 2
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "UnqualifiedGeometry", HasOutput, TmpPath)
