from dataclasses import replace as Replace

from convert.formats.Fusion.Extrudes.Cut.CutEndData import CutEndData
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureExtrude import ExtrudeFeature
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.records.RecordProvenance import Provenance, ProvenanceSpan


# the typed end retains the separate archived control and its bound source evidence
def RetainCutEnd(
    StepValue: FeatureStep,
    Origin: Provenance,
    Fields: CutEndData,
    Definition: ExtrudeFeature,
    DepthId: str | None,
    PickValue: Selection | None,
    Spans: tuple[ProvenanceSpan, ...],
) -> FeatureStep:
    Attributes: dict[str, object] = {
        **StepValue.attributes,
        "fusion.extrude.end_flags": Fields.FlagBits,
        "fusion.extrude.native_direction": (
            Fields.Direction.x,
            Fields.Direction.y,
            Fields.Direction.z,
        ),
    }
    if DepthId is not None:
        Attributes["fusion.extrude.along_parameter_id"] = DepthId
    if PickValue is not None:
        Attributes["fusion.extrude.end_selector_id"] = PickValue.id
    return Replace(
        StepValue,
        definition=Definition,
        selection_ids=StepValue.selection_ids
        + (() if PickValue is None else (PickValue.id,)),
        provenance=Replace(Origin, spans=Origin.spans + Spans),
        attributes=FreezeMapping(Attributes),
    )
