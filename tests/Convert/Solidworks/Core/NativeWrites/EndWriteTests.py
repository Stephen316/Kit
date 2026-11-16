from pathlib import Path as FilePath

from pytest import mark as TestMark

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from tests.Convert.Solidworks.Core.NativeWrites.EndEvidence import EndEvidence
from tests.Convert.Solidworks.Core.NativeWrites.RejectFields import RejectFields


# unknown end modes must fail consistently for both nesting and suppression states
@TestMark.parametrize("Family", ("extrude", "second", "hole"))
@TestMark.parametrize(
    "EndValue", (ExtrudeEnd.NATIVE, "native:32767", "future:termination")
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestEndWrite(
    TmpPath: FilePath,
    Family: str,
    EndValue: ExtrudeEnd | str,
    IsNested: bool,
    IsSuppressed: bool,
) -> None:
    RejectFields(EndEvidence(Family, EndValue, IsSuppressed), TmpPath, IsNested)


# depthless through all is valid neutral history while destination reconstruction still needs qualification
@TestMark.parametrize(("IsNested", "IsSuppressed"), ((False, False), (True, True)))
def TestDepthless(TmpPath: FilePath, IsNested: bool, IsSuppressed: bool) -> None:
    Document = EndEvidence("depthless", ExtrudeEnd.THROUGH_ALL, IsSuppressed)
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    assert any(
        isinstance(StepValue.definition, ExtrudeFeature)
        and StepValue.definition.length is None
        for StepValue in Restored.feature_timeline
    )
    RejectFields(
        Document, TmpPath, IsNested, "depthless extrusion reconstruction is unqualified"
    )
