# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


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
    RevExpressionsMut,
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
    Plan: BodyRevPlan,
    Cache: BodyRevCache,
    DepthRef: str,
) -> Object:
    Source = Plan.Extrude
    Direction = (Source.Direction.x, Source.Direction.y, Source.Direction.z)
    Seed = AddExtToolMut(
        Context, FeatureInfo, Direction, Source.DistanceMm, 0.0, False, DepthRef
    )
    Expressions = [
        ("Dir", BodyDepthDir(Direction, DepthRef)),
        ("LengthFwd", DepthRef),
    ]
    ReplaceNameMut(Seed.properties, "ExpressionEngine", ExpressionProp(Expressions))
    ShapeEntry = AddBrepEntryMut(Features.PayloadEntries, Seed.name, Cache.Extrude)
    ReplaceNameMut(Seed.properties, "Shape", ShapeProp(ShapeEntry))
    ReplaceNameMut(Sketch.properties, "Visibility", BoolProp("Visibility", False))
    SetProfRulesMut(Context, Geometry, Sketch, Source.SketchId)
    TrackSolidMut(Features, FeatureInfo, Seed)
    Features.EditableBodySeed = FeatureInfo.FeatureId
    return Seed


# the downstream native feature links the exact upstream subelement and owns a separate solid
def AddBodyTurnMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    FeatureInfo: FeatureData,
    Profile: Object,
    Seed: Object,
    Plan: BodyRevPlan,
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
                AxisSketch=Seed.name,
                AxisSub=Cache.EdgeName,
            ),
            ExpressionProp([("Angle", Expression)]),
            ShapeProp(ShapeEntry),
            *FeatureMeta(FeatureInfo.Source, "feature"),
            BoolProp("Visibility", True),
        ]
    )
    Revolution.dependencies.extend((Profile.name, Context.ParamSheet.name, Seed.name))
    ReplaceNameMut(Profile.properties, "Visibility", BoolProp("Visibility", False))
    SetProfRulesMut(
        Context, Geometry, Profile, Plan.Revolve.SketchId, Plan.ProfilePairs
    )
    TrackSolidMut(Features, FeatureInfo, Revolution)
    Features.FinalShapeFile = ShapeEntry
    Features.EditableRevId = FeatureInfo.FeatureId
    Features.RevBinding = KBodyRevBinding
    Features.BodyAxisTarget = (Plan.AxisEdgeId, Seed.name, Cache.EdgeName)


# the linked edit graph can replace the carrier only when both native seeds are ready
def HasBodyRevMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Document: CadDocument | None,
) -> bool:
    if Document is None or len(Features.FeatureItems) != 4:
        return False
    Plan = ReadBodyRev(Document, Document.feature_timeline[-1])
    if Plan is None:
        return False
    SourceStep, SeedStep, ProfileStep, TurnStep = Features.FeatureItems
    SeedInfo = FeatureDataOf(Geometry, Features, SeedStep)
    TurnInfo = FeatureDataOf(Geometry, Features, TurnStep)
    SeedSketch = EditProfile(Context, Geometry, SeedInfo, Plan.Extrude.SketchId)
    Profile = EditProfile(Context, Geometry, TurnInfo, Plan.Revolve.SketchId)
    DepthRef = Context.Parameters.expression(Plan.Extrude.ParameterId)
    Angles = RevExpressionsMut(Context, Plan.Revolve)
    if (
        SeedInfo.FeatureId != Plan.ExtrudeId
        or TurnInfo.FeatureId != Plan.RevolveId
        or SeedSketch is None
        or Profile is None
        or not DepthRef
        or len(Angles) != 1
        or not (ProfileLines := GetProfLines(Profile))
        or (Cache := BuildBodyCache(Document, Plan)) is None
    ):
        return False
    AddFeatureMut(Context, Geometry, Features, SourceStep)
    Seed = AddBodySeedMut(
        Context, Geometry, Features, SeedInfo, SeedSketch, Plan, Cache, DepthRef
    )
    AddFeatureMut(Context, Geometry, Features, ProfileStep)
    Expression = BodyAngleExpr(
        Seed.name, Cache.EdgeName, Profile.name, ProfileLines, Angles[0][1], DepthRef
    )
    AddBodyTurnMut(
        Context, Geometry, Features, TurnInfo, Profile, Seed, Plan, Cache, Expression
    )
    return True
