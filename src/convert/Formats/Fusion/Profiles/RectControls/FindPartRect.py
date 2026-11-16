from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch


# independent principal rectangles admit one sketch and at most its directly consuming boss
def FindPartRect(
    Document: CadDocument, History: HistoryPart
) -> tuple[Sketch, FeatureStep | None] | None:
    Steps = Document.feature_timeline
    if (
        Document.assembly is not None
        or len(Document.sketches) != 1
        or len(Steps) not in (1, 2)
    ):
        return None
    SketchValue = Document.sketches[0]
    SketchStep = Steps[0]
    Origin = SketchStep.provenance
    if (
        Origin is None
        or not Origin.spans
        or Origin.spans[0].record_kind != KSketchFeature
        or SketchStep.sketch_id != SketchValue.id
        or len(SketchValue.entities) != 9
        or len(SketchValue.constraints) != 7
        or SketchValue.suppressed
        or tuple(
            int(Value.provenance.native_id)
            for Value in Steps
            if Value.provenance is not None
        )
        != History.EntryIds
    ):
        return None
    Frames = {Value.id: Value for Value in Document.support_planes}
    Frame = Frames[SketchValue.support_plane_id]
    if Frame.attributes.get(
        "fusion.native_support_resolved"
    ) is not True or Frame.attributes.get("fusion.native_support_name") not in (
        "XY",
        "YZ",
    ):
        return None
    if len(Steps) == 1:
        return SketchValue, None
    Feature = Steps[1]
    if (
        Feature.kind != FeatureKind.KExtrusion
        or Feature.operation != BooleanOp.KCreate
        or not isinstance(Feature.definition, DistanceExtrude)
        or Feature.sketch_id != SketchValue.id
        or SketchStep.id not in Feature.input_feature_ids
        or Feature.suppressed
    ):
        return None
    return SketchValue, Feature
