from convert.adapters.freecad.Archive import (
    AddBrepEntryMut,
    AddExtToolMut,
    BoolProp,
    DocContext,
    DocFeatures,
    DocGeometry,
    ExpressionProp,
    Object,
    ReplaceNameMut,
    SetProfRulesMut,
    ShapeProp,
    TrackSolidMut,
)
from convert.adapters.freecad.EditBodyRev.BodyRevExpr import BodyDepthDir
from convert.adapters.freecad.EditScale.ScaleCache import ScaleCache


# hidden upstream extrusions retain the native profile and independently writable depth
def AddScaleSeedMut(
    Context: DocContext, Geometry: DocGeometry, Features: DocFeatures, Cache: ScaleCache
) -> Object:
    AxisValue = (0.0, 0.0, 1.0)
    SeedValue = AddExtToolMut(
        Context, Cache.Feature, AxisValue, Cache.Body.Depth, 0.0, False, Cache.DepthRef
    )
    ReplaceNameMut(
        SeedValue.properties,
        "ExpressionEngine",
        ExpressionProp(
            [
                ("Dir", BodyDepthDir(AxisValue, Cache.DepthRef, Cache.Sketch.name)),
                ("LengthFwd", Cache.DepthRef),
            ]
        ),
    )
    Entry = AddBrepEntryMut(Features.PayloadEntries, SeedValue.name, Cache.SourceBrep)
    ReplaceNameMut(SeedValue.properties, "Shape", ShapeProp(Entry))
    ReplaceNameMut(SeedValue.properties, "Visibility", BoolProp("Visibility", False))
    ReplaceNameMut(Cache.Sketch.properties, "Visibility", BoolProp("Visibility", False))
    SetProfRulesMut(Context, Geometry, Cache.Sketch, Cache.Body.SketchId)
    TrackSolidMut(Features, Cache.Feature, SeedValue)
    return SeedValue
