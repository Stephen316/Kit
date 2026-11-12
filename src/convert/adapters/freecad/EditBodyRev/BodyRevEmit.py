from convert.adapters.freecad.Archive import (
    AddBrepEntryMut,
    AddExtToolMut,
    AddFeatureMut,
    BoolProp,
    DocContext,
    DocFeatures,
    DocGeometry,
    EditProfile,
    ExpressionProp,
    FeatureData,
    FeatureDataOf,
    FeatureMeta,
    GetProfLines,
    Object,
    ReplaceNameMut,
    SetRevExprMut,
    SetProfRulesMut,
    ShapeProp,
    StringProp,
    TrackSolidMut,
)
from convert.adapters.freecad.EditBodyRev.BodyRevBinding import KBodyRevBinding
from convert.adapters.freecad.EditBodyRev.BodyRevCache import (
    BodyRevCache,
    BuildBodyCache,
)
from convert.adapters.freecad.EditBodyRev.BodyRevExpr import BodyAngleExpr, BodyDepthDir
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan, ReadBodyRev
from convert.adapters.freecad.EditRev.RevolveProps import MakeRevProps
from interchange.document.models.DocumentModel import CadDocument


# the upstream solid retains its sketch incidence and owns the linked edge cache
def AddBodySeedMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    FeatureInfo: FeatureData,
    Sketch: Object,
    PlanValue: BodyRevPlan,
    Cache: BodyRevCache,
    DepthRef: str,
) -> Object:
    Source = PlanValue.Extrude
    Direction = (Source.Direction.x, Source.Direction.y, Source.Direction.z)
    SeedValue = AddExtToolMut(
        Context, FeatureInfo, Direction, Source.DistanceMm, 0.0, False, DepthRef
    )
    Expressions = [
        ("Dir", BodyDepthDir(Direction, DepthRef, Sketch.name)),
        ("LengthFwd", DepthRef),
    ]
    ReplaceNameMut(
        SeedValue.properties, "ExpressionEngine", ExpressionProp(Expressions)
    )
    ShapeEntry = AddBrepEntryMut(Features.PayloadEntries, SeedValue.name, Cache.Extrude)
    ReplaceNameMut(SeedValue.properties, "Shape", ShapeProp(ShapeEntry))
    ReplaceNameMut(Sketch.properties, "Visibility", BoolProp("Visibility", False))
    SetProfRulesMut(Context, Geometry, Sketch, Source.SketchId)
    TrackSolidMut(Features, FeatureInfo, SeedValue)
    Features.EditableBodySeed = FeatureInfo.FeatureId
    return SeedValue


# the downstream native feature links the exact upstream subelement and owns a separate solid
def AddBodyTurnMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    FeatureInfo: FeatureData,
    Profile: Object,
    SeedValue: Object,
    PlanValue: BodyRevPlan,
    Cache: BodyRevCache,
    Expression: str,
) -> None:
    Revolution = Context.Graph.add(
        "Part::Revolution", FeatureInfo.FeatureName, "Revolution", Touched=True
    )
    ShapeEntry = AddBrepEntryMut(
        Features.PayloadEntries, Revolution.name, Cache.Revolve
    )
    Revolution.properties.extend(
        [
            StringProp("Label", FeatureInfo.FeatureName),
            *MakeRevProps(
                Profile.name,
                Cache.Base,
                Cache.Axis,
                Cache.AngleDeg,
                AxisSketch=SeedValue.name,
                AxisSub=Cache.EdgeName,
            ),
            ExpressionProp([("Angle", Expression)]),
            ShapeProp(ShapeEntry),
            *FeatureMeta(FeatureInfo.Source, "feature"),
            BoolProp("Visibility", True),
        ]
    )
    Revolution.dependencies.extend(
        (Profile.name, Context.ParamSheet.name, SeedValue.name)
    )
    ReplaceNameMut(Profile.properties, "Visibility", BoolProp("Visibility", False))
    SetProfRulesMut(
        Context, Geometry, Profile, PlanValue.Revolve.SketchId, PlanValue.ProfilePairs
    )
    TrackSolidMut(Features, FeatureInfo, Revolution)
    Features.FinalShapeFile = ShapeEntry
    Features.EditableRevId = FeatureInfo.FeatureId
    Features.RevBinding = KBodyRevBinding
    Features.BodyAxisTarget = (PlanValue.AxisEdgeId, SeedValue.name, Cache.EdgeName)


# the linked edit graph can replace the carrier only when both native seeds are ready
def HasBodyRevMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Document: CadDocument | None,
) -> bool:
    if Document is None or len(Features.FeatureItems) != 4:
        return False
    PlanValue = ReadBodyRev(Document, Document.feature_timeline[-1])
    if PlanValue is None:
        return False
    SourceStep, SeedStep, ProfileStep, TurnStep = Features.FeatureItems
    SeedInfo = FeatureDataOf(Geometry, Features, SeedStep)
    TurnInfo = FeatureDataOf(Geometry, Features, TurnStep)
    SeedSketch = EditProfile(Context, Geometry, SeedInfo, PlanValue.Extrude.SketchId)
    Profile = EditProfile(Context, Geometry, TurnInfo, PlanValue.Revolve.SketchId)
    DepthRef = Context.Parameters.expression(PlanValue.Extrude.ParameterId)
    Angles = SetRevExprMut(Context, PlanValue.Revolve)
    if (
        SeedInfo.FeatureId != PlanValue.ExtrudeId
        or TurnInfo.FeatureId != PlanValue.RevolveId
        or SeedSketch is None
        or Profile is None
        or not DepthRef
        or len(Angles) != 1
        or not (ProfileLines := GetProfLines(Profile))
    ):
        return False
    Cache = BuildBodyCache(Document, PlanValue)
    AddFeatureMut(Context, Geometry, Features, SourceStep)
    SeedValue = AddBodySeedMut(
        Context, Geometry, Features, SeedInfo, SeedSketch, PlanValue, Cache, DepthRef
    )
    AddFeatureMut(Context, Geometry, Features, ProfileStep)
    Expression = BodyAngleExpr(
        SeedValue.name,
        Cache.EdgeName,
        Profile.name,
        ProfileLines,
        Angles[0][1],
        DepthRef,
    )
    AddBodyTurnMut(
        Context,
        Geometry,
        Features,
        TurnInfo,
        Profile,
        SeedValue,
        PlanValue,
        Cache,
        Expression,
    )
    return True
