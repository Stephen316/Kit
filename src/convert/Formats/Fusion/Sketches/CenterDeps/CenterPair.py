from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Sketches.FaceSupport.FaceProjection import FaceTargets
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane


# the scoped center proof needs both the consuming sketch and the earlier boss sketch
@MakeDataClass(frozen=True, slots=True)
class CenterPair:
    CutSketch: Sketch
    BossSketch: Sketch
    Frame: SupportPlane
    BodyId: int
    ComponentId: int
    CutterStep: FeatureStep
    BossStep: FeatureStep


# a saved historical target chooses the driver sketch independently of parameter names
def FindCenterPair(Document: CadDocument) -> CenterPair | None:
    Targets = FaceTargets(Document)
    if len(Targets) != 1 or len(next(iter(Targets.values()))) != 1:
        return None
    ((Target, Cutter),) = next(iter(Targets.values()))
    BodyId = Target.query.get("native_body_id")
    ComponentId = Target.query.get("native_component_id")
    Features = {Value.id: Value for Value in Document.feature_timeline}
    SourceId = Target.query.get("source_feature_id")
    Source = Features.get(SourceId) if isinstance(SourceId, str) else None
    if (
        Source is None
        or Source.kind != FeatureKind.KExtrusion
        or Source.operation != BooleanOp.KCreate
        or Source.order >= Cutter.order
        or type(BodyId) is not int
        or type(ComponentId) is not int
    ):
        return None
    Sketches = {Value.id: Value for Value in Document.sketches}
    CutSketch = Sketches.get(Cutter.sketch_id or "")
    BossSketch = Sketches.get(Source.sketch_id or "")
    if CutSketch is None or BossSketch is None or CutSketch.id == BossSketch.id:
        return None
    Frames = {Value.id: Value for Value in Document.support_planes}
    Frame = Frames[CutSketch.support_plane_id]
    if (
        Frame.attributes.get("fusion.native_support_kind")
        != "historical_face_occurrence"
        or Frame.attributes.get("fusion.component_object_id") != ComponentId
        or Frames[BossSketch.support_plane_id].attributes.get(
            "fusion.component_object_id"
        )
        != ComponentId
    ):
        return None
    return CenterPair(CutSketch, BossSketch, Frame, BodyId, ComponentId, Cutter, Source)
