# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass, replace as Replace

from convert.adapters.freecad.Archive import (
    DocContext,
    DocFeatures,
    DocGeometry,
    FeatureData,
    FeatureDataOf,
    Object,
)
from convert.adapters.freecad.EditScale.ScaleCache import MakeScaleCache, ScaleCache
from convert.adapters.freecad.EditScale.ScaleExpressions import ScaleOffset
from convert.adapters.freecad.EditScale.ScalePointEmit import FindScalePoint
from convert.adapters.freecad.EditScale.ScaleWritePlan import ScaleWritePlan
from interchange.geometry.models.VectorSpace import SpaceVector


# graph mutation starts only after every dependency and cache is ready
@MakeDataClass(frozen=True, slots=True)
class ScalePreflight:
    Step: FeatureData
    Bodies: tuple[ScaleCache, ...]
    Refs: tuple[str, ...]
    Translation: SpaceVector
    PointSketch: tuple[Object, int] | None


# resolve the native objects against the same manifest used to write the target graph
def PrepScale(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Plan: ScaleWritePlan,
) -> ScalePreflight | None:
    Items = {
        Value["id"]: Value
        for Value in Features.FeatureItems
        if isinstance(Value.get("id"), str)
    }
    Item = Items.get(Plan.FeatureId)
    if Item is None:
        return None
    PointSketch = None
    if Plan.Center.SketchId:
        PointSketch = FindScalePoint(Context, Geometry, Plan.Center)
        if PointSketch is None or (
            Plan.Center.FeatureId and Plan.Center.FeatureId not in Items
        ):
            return None
    Refs = tuple(Context.Parameters.expression(Identity) for Identity in Plan.FactorIds)
    if not all(Refs):
        return None
    FactorRefs = tuple(Ref for Ref in Refs if Ref)
    Translation = ScaleOffset(Plan.Center.Point, Plan.Factors)
    Caches = []
    for Body in Plan.Bodies:
        Source = Items.get(Body.SourceId)
        if Source is None:
            return None
        Feature = Replace(FeatureDataOf(Geometry, Features, Source), BaseName="")
        Cache = MakeScaleCache(Context, Geometry, Feature, Body, Translation)
        if Cache is None:
            return None
        Caches.append(Cache)
    return ScalePreflight(
        FeatureDataOf(Geometry, Features, Item),
        tuple(Caches),
        FactorRefs,
        Translation,
        PointSketch,
    )
