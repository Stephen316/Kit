from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.Archive import (
    DocContext,
    DocGeometry,
    EditProfile,
    FeatureData,
    Object,
)
from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditScale.ScaleBodyPlan import ScaleBodyPlan
from interchange.geometry.models.VectorSpace import SpaceVector


# preflight finishes both native caches and resolves every source link before emission
@MakeDataClass(frozen=True, slots=True)
class ScaleCache:
    Body: ScaleBodyPlan
    Feature: FeatureData
    Sketch: Object
    DepthRef: str
    SourceBrep: bytes
    ResultBrep: bytes


# a root location translates the native cache without baking the center into its vertices
def MakeScaleCache(
    Context: DocContext,
    Geometry: DocGeometry,
    Feature: FeatureData,
    PlanValue: ScaleBodyPlan,
    Translation: SpaceVector,
) -> ScaleCache | None:
    Sketch = EditProfile(Context, Geometry, Feature, PlanValue.SketchId)
    DepthRef = Context.Parameters.expression(PlanValue.DepthId)
    if Sketch is None or not DepthRef:
        return None
    Source = BrepModelBrep(PlanValue.SourceModel)
    Result = BrepModelBrep(PlanValue.ResultModel, RootTranslation=Translation)
    if not Source or not Result:
        return None
    return ScaleCache(PlanValue, Feature, Sketch, DepthRef, Source, Result)
