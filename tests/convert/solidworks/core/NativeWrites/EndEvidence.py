from dataclasses import replace as ReplaceData

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureKinds import HoleFeature
from tests.convert.api.Fusion.AdapterCases import AdapterCase


# termination fixtures isolate unsupported end modes from other semantic evidence
def EndEvidence(
    Family: str, EndValue: ExtrudeEnd | str, IsSuppressed: bool
) -> CadDocument:
    Document = AdapterCase("cuboid")
    Original = next(
        StepValue
        for StepValue in Document.feature_timeline
        if isinstance(StepValue.definition, DistanceExtrude)
    )
    DistanceValue = Original.definition
    assert isinstance(DistanceValue, DistanceExtrude)
    LengthValue = next(
        Parameter.value
        for Parameter in Document.parameters
        if Parameter.id == DistanceValue.AlongParameterId
    )
    Definition = ExtrudeFeature(
        LengthValue,
        direction=DistanceValue.Direction,
    )
    if Family == "hole":
        Changed = ReplaceData(
            Original,
            kind=FeatureKind.HOLE,
            definition=HoleFeature(LengthValue, LengthValue, EndValue),
        )
    elif Family == "second":
        Changed = ReplaceData(
            Original, definition=ReplaceData(Definition, second_end_condition=EndValue)
        )
    else:
        Changed = ReplaceData(
            Original,
            definition=ReplaceData(
                Definition,
                length=None if Family == "depthless" else LengthValue,
                end_condition=EndValue,
            ),
        )
    Changed = ReplaceData(Changed, suppressed=IsSuppressed)
    return ReplaceData(
        Document,
        feature_timeline=tuple(
            Changed if StepValue.id == Original.id else StepValue
            for StepValue in Document.feature_timeline
        ),
    )
