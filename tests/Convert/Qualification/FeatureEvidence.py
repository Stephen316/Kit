from dataclasses import replace as ReplaceData
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureKinds import CombineFeature
from interchange.Features.FeatureStep import FeatureStep
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# distinct feature evidence isolates unresolved history from unrelated source capabilities
def FeatureEvidence(ModeValue: str) -> CadDocument:
    Document = AdapterCase("rectangle")
    StepValue = FeatureStep(
        "evidence:feature", "Required semantics", FeatureKind.NATIVE, 0
    )
    if ModeValue == "kind":
        StepValue = ReplaceData(StepValue, kind="future:feature")
    if ModeValue == "operation":
        StepValue = ReplaceData(
            StepValue, kind=FeatureKind.BOOLEAN, operation="future:boolean"
        )
    if ModeValue == "combine":
        StepValue = ReplaceData(
            StepValue,
            kind=FeatureKind.BOOLEAN,
            definition=CombineFeature(operation=CastValue(BooleanOp, "future:boolean")),
        )
    return ReplaceData(Document, feature_timeline=(StepValue,))
