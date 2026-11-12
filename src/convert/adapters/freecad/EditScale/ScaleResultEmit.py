from convert.adapters.freecad.Archive import (
    AddBrepEntryMut,
    BoolProp,
    DocContext,
    DocFeatures,
    ExpressionProp,
    FeatureData,
    FeatureMeta,
    FloatProp,
    LinkProp,
    MakePlacement,
    Object,
    SetDocGroupMut,
    ShapeProp,
    StringProp,
    TrackSolidMut,
)
from convert.adapters.freecad.EditScale.ScaleCache import ScaleCache
from convert.adapters.freecad.EditScale.ScaleExpressions import ScaleExprs
from interchange.geometry.models.VectorSpace import SpaceVector


# each result has a native source link and one independently seeded shape
def AddScaleResMut(
    Context: DocContext,
    Features: DocFeatures,
    Feature: FeatureData,
    SeedValue: Object,
    Cache: ScaleCache,
    References: tuple[str, ...],
    Factors: SpaceVector,
    Translation: SpaceVector,
    PointName: str,
    SoleResult: bool,
) -> Object:
    Label = (
        Feature.FeatureName
        if SoleResult
        else f"{Feature.FeatureName} - {Cache.Feature.FeatureName}"
    )
    Result = Context.Graph.add("Part::Scale", Label, "Scale", Touched=True)
    Entry = AddBrepEntryMut(Features.PayloadEntries, Result.name, Cache.ResultBrep)
    Result.properties.extend(
        [
            StringProp("Label", Label),
            LinkProp("Base", SeedValue.name),
            BoolProp("Uniform", len(References) == 1),
            FloatProp("UniformScale", Factors.x if len(References) == 1 else 1.0),
            FloatProp("XScale", Factors.x),
            FloatProp("YScale", Factors.y),
            FloatProp("ZScale", Factors.z),
            MakePlacement(
                "Placement",
                {
                    "origin": {
                        "x": Translation.x,
                        "y": Translation.y,
                        "z": Translation.z,
                    }
                },
            ),
            ExpressionProp(ScaleExprs(References, PointName)),
            ShapeProp(Entry),
            StringProp("KitBodyId", Cache.Body.BodyId, Dynamic=True),
            BoolProp("Visibility", True),
        ]
    )
    Result.dependencies.extend((SeedValue.name, Context.ParamSheet.name))
    if PointName:
        Result.dependencies.append(PointName)
    if SoleResult:
        Result.properties.extend(FeatureMeta(Feature.Source, "feature"))
        Features.FinalShapeFile = Entry
    Features.ScaleBodyTips[Cache.Body.BodyId] = Result.name
    return Result


# a multi body scale retains one timeline owner while each wrapper links its own result
def TrackScaleMut(
    Context: DocContext,
    Features: DocFeatures,
    Feature: FeatureData,
    Results: tuple[Object, ...],
) -> None:
    if len(Results) == 1:
        Owner = Results[0]
    else:
        Owner = Context.Graph.add(
            "App::DocumentObjectGroup", Feature.FeatureName, "Scale"
        )
        SetDocGroupMut(
            Owner, Feature.FeatureName, [Value.name for Value in Results], True
        )
        Owner.properties.extend(FeatureMeta(Feature.Source, "feature"))
    TrackSolidMut(Features, Feature, Owner)
