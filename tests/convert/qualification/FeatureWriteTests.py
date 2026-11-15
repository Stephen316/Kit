from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.api.Fusion.AdapterCases import AdapterCase
from tests.convert.qualification.FeatureEvidence import FeatureEvidence
from tests.convert.qualification.RejectPublic import RejectPublic
from tests.convert.solidworks.core.NestedDocument import NestedDocument


@TestMark.parametrize("ModeValue", ("native", "kind", "operation", "combine"))
@TestMark.parametrize("IsNested", (False, True))
def TestFeatureGate(TmpPath: FilePath, ModeValue: str, IsNested: bool) -> None:
    Document = FeatureEvidence(ModeValue)
    if IsNested:
        Document = NestedDocument(AdapterCase("rectangle"), Document)
    RejectPublic(Document, TmpPath)
