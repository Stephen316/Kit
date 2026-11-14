from convert.adapters.Fusion.Authoring.MakePartSteps import MakePartSteps
from convert.adapters.Fusion.Authoring.ProfileShape import HasSolid
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.VectorSpace import SpaceVector


def MakeFeatures(SpecValue: DocumentSpec) -> tuple[FeatureStep, ...]:
    if SpecValue.ProfileKind == "parameter":
        return ()
    Params = (
        ("width-dimension", "depth-dimension") if SpecValue.ConstrainRectangle else ()
    )
    SketchStep = FeatureStep(
        "sketch",
        SpecValue.SketchName,
        FeatureKind.KReference,
        0,
        sketch_id="sketch",
        parameter_ids=Params,
    )
    if not HasSolid(SpecValue):
        return (SketchStep,)
    Definition = DistanceExtrude(
        "along", SpaceVector(0.0, 0.0, 1.0), TaperParameterId="taper"
    )
    ExtrudeStep = FeatureStep(
        "extrude",
        SpecValue.ExtrusionName,
        FeatureKind.KExtrusion,
        1,
        ("sketch",),
        "sketch",
        ("along", "taper"),
        BooleanOp.KCreate,
        Definition,
    )
    return (SketchStep, ExtrudeStep, *MakePartSteps(SpecValue))
