from dataclasses import replace as Replace

from convert.formats.Fusion.Extrudes.NativeExtrude import NativeExtrude
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordProvenance import Provenance


# trace the saved directional controls without storing a second evaluated depth
def RetainExtProof(
    StepValue: FeatureStep,
    Definition: DistanceExtrude,
    Origin: Provenance,
    Native: NativeExtrude,
    Owners: dict[int, RecordSpan],
    Along: Parameter,
    FrameId: str,
    Occurrences: tuple[int, ...] | None,
) -> FeatureStep:
    Spans = Origin.spans
    for Identity in (Native.ProxyId, Native.CacheId, Native.AlongId):
        Spans += tuple(
            Value for Value in ParamOrigin(Owners[Identity]).spans if Value not in Spans
        )
    if Along.provenance is not None:
        Spans += tuple(Value for Value in Along.provenance.spans if Value not in Spans)
    Attributes: dict[str, object] = {
        **StepValue.attributes,
        "fusion.extrude.native_direction": Native.Direction,
        "fusion.extrude.start_kind": (
            "profile_plane" if Native.StartId is None else "profile_offset"
        ),
        "fusion.extrude.start_frame_id": FrameId,
        "fusion.extrude.end_kind": "distance",
        "fusion.extrude.along_binding_object_id": Native.AlongId,
        "fusion.extrude.cache_object_id": Native.CacheId,
    }
    if Occurrences is not None:
        Attributes["fusion.extrude.authoring_occurrences"] = Occurrences
    return Replace(
        StepValue,
        operation=BooleanOp.KCreate,
        definition=Definition,
        provenance=Replace(Origin, spans=Spans),
        attributes=FreezeMapping(Attributes),
    )
