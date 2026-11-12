from convert.adapters.freecad.Archive import (
    DocContext,
    DocFeatures,
    DocGeometry,
    Object,
    TextAction,
)
from convert.adapters.freecad.EditScale.ScalePointEmit import AddScalePtMut
from convert.adapters.freecad.EditScale.ScalePreflight import PrepScale
from convert.adapters.freecad.EditScale.ScaleResultEmit import (
    AddScaleResMut,
    TrackScaleMut,
)
from convert.adapters.freecad.EditScale.ScaleSeedEmit import AddScaleSeedMut
from convert.adapters.freecad.EditScale.ScaleSketchEmit import TrackSketchMut
from convert.adapters.freecad.EditScale.ScaleWritePlan import GetScalePlan
from interchange.document.models.DocumentModel import CadDocument


# the live archive retains the original source steps and the result body tip order
def HasScaleMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Document: CadDocument | None,
) -> bool:
    if Document is None:
        return False
    if (PlanValue := GetScalePlan(Document)) is None:
        return False
    if (Prepared := PrepScale(Context, Geometry, Features, PlanValue)) is None:
        raise ValueError("FreeCAD editable Scale native graph could not be prepared")
    CacheBySource = {Value.Body.SourceId: Value for Value in Prepared.Bodies}
    Sketches = {Value.Body.SketchId: Value.Sketch for Value in Prepared.Bodies}
    if Prepared.PointSketch is not None:
        Sketches[PlanValue.Center.SketchId] = Prepared.PointSketch[0]
    Seeds: dict[str, Object] = {}
    CenterName = ""
    for ItemValue in Features.FeatureItems:
        Identity = TextAction(ItemValue.get("id"))
        if Identity == PlanValue.FeatureId:
            continue
        if Identity in CacheBySource:
            Seeds[Identity] = AddScaleSeedMut(
                Context, Geometry, Features, CacheBySource[Identity]
            )
        elif (
            Identity == PlanValue.Center.FeatureId and Prepared.PointSketch is not None
        ):
            CenterName = AddScalePtMut(
                Context, Features, PlanValue.Center, *Prepared.PointSketch, ItemValue
            ).name
        else:
            TrackSketchMut(
                Features,
                Geometry,
                Sketches[TextAction(ItemValue.get("sketch_id"))],
                Identity,
                ItemValue,
            )
    if not CenterName and Prepared.PointSketch is not None:
        CenterName = AddScalePtMut(
            Context, Features, PlanValue.Center, *Prepared.PointSketch, None
        ).name
    Results = tuple(
        AddScaleResMut(
            Context,
            Features,
            Prepared.Step,
            Seeds[Cache.Body.SourceId],
            Cache,
            Prepared.Refs,
            PlanValue.Factors,
            Prepared.Translation,
            CenterName,
            len(Prepared.Bodies) == 1,
        )
        for Cache in Prepared.Bodies
    )
    TrackScaleMut(Context, Features, Prepared.Step, Results)
    Features.EditableScaleSteps = tuple(
        TextAction(ItemValue.get("id")) for ItemValue in Features.FeatureItems
    )
    return True
