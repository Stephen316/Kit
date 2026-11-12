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
    PlanValue: ScaleWritePlan,
) -> ScalePreflight | None:
    Items = {
        Value["id"]: Value
        for Value in Features.FeatureItems
        if isinstance(Value.get("id"), str)
    }
    ItemValue = Items.get(PlanValue.FeatureId)
    if ItemValue is None:
        return None
    PointSketch = None
    if PlanValue.Center.SketchId:
        PointSketch = FindScalePoint(Context, Geometry, PlanValue.Center)
        if PointSketch is None or (
            PlanValue.Center.FeatureId and PlanValue.Center.FeatureId not in Items
        ):
            return None
    References = tuple(
        Context.Parameters.expression(Identity) for Identity in PlanValue.FactorIds
    )
    if not all(References):
        return None
    FactorRefs = tuple(
        ReferenceValue for ReferenceValue in References if ReferenceValue
    )
    Translation = ScaleOffset(PlanValue.Center.Point, PlanValue.Factors)
    Caches: list[ScaleCache] = []
    for BodyValue in PlanValue.Bodies:
        Source = Items.get(BodyValue.SourceId)
        if Source is None:
            return None
        Feature = Replace(FeatureDataOf(Geometry, Features, Source), BaseName="")
        Cache = MakeScaleCache(Context, Geometry, Feature, BodyValue, Translation)
        if Cache is None:
            return None
        Caches.append(Cache)
    return ScalePreflight(
        FeatureDataOf(Geometry, Features, ItemValue),
        tuple(Caches),
        FactorRefs,
        Translation,
        PointSketch,
    )
