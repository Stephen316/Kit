from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Api.Fusion.AdapterCases import AdapterCase
from tests.Convert.Qualification.FeatureEvidence import FeatureEvidence
from tests.Convert.Qualification.RejectPublic import RejectPublic
from tests.Convert.Solidworks.Core.NestedDocument import NestedDocument


# unresolved feature semantics must remain disqualifying at each assembly nesting level
@TestMark.parametrize("ModeValue", ("native", "kind", "operation", "combine"))
@TestMark.parametrize("IsNested", (False, True))
def TestFeatureGate(TmpPath: FilePath, ModeValue: str, IsNested: bool) -> None:
    Document = FeatureEvidence(ModeValue)
    if IsNested:
        Document = NestedDocument(AdapterCase("rectangle"), Document)
    RejectPublic(Document, TmpPath)
