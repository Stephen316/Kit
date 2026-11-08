# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
    Seed: Object,
    Cache: ScaleCache,
    Refs: tuple[str, ...],
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
            LinkProp("Base", Seed.name),
            BoolProp("Uniform", len(Refs) == 1),
            FloatProp("UniformScale", Factors.x if len(Refs) == 1 else 1.0),
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
            ExpressionProp(ScaleExprs(Refs, PointName)),
            ShapeProp(Entry),
            StringProp("KitBodyId", Cache.Body.BodyId, Dynamic=True),
            BoolProp("Visibility", True),
        ]
    )
    Result.dependencies.extend((Seed.name, Context.ParamSheet.name))
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
