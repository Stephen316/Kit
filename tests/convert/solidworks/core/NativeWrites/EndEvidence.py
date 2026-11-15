from dataclasses import replace as ReplaceData

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureKinds import HoleFeature
from tests.convert.api.Fusion.AdapterCases import AdapterCase


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
    Definition = ExtrudeFeature(
        next(
            Parameter.value
            for Parameter in Document.parameters
            if Parameter.id == DistanceValue.AlongParameterId
        ),
        direction=DistanceValue.Direction,
    )
    if Family == "hole":
        Changed = ReplaceData(
            Original,
            kind=FeatureKind.HOLE,
            definition=HoleFeature(Definition.length, Definition.length, EndValue),
        )
    elif Family == "second":
        Changed = ReplaceData(
            Original, definition=ReplaceData(Definition, second_end_condition=EndValue)
        )
    else:
        Changed = ReplaceData(
            Original, definition=ReplaceData(Definition, end_condition=EndValue)
        )
    Changed = ReplaceData(Changed, suppressed=IsSuppressed)
    return ReplaceData(
        Document,
        feature_timeline=tuple(
            Changed if StepValue.id == Original.id else StepValue
            for StepValue in Document.feature_timeline
        ),
    )
