# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.Archive import (
    DocContext,
    DocFeatures,
    DocGeometry,
    Object,
    TextAction,
)
from convert.adapters.freecad.EditScale.ScalePointEmit import AddScalePointMut
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
    Plan = GetScalePlan(Document)
    Prep = PrepScale(Context, Geometry, Features, Plan) if Plan is not None else None
    if Plan is None or Prep is None:
        return False
    CacheBySource = {Value.Body.SourceId: Value for Value in Prep.Bodies}
    Sketches = {Value.Body.SketchId: Value.Sketch for Value in Prep.Bodies}
    if Prep.PointSketch is not None:
        Sketches[Plan.Center.SketchId] = Prep.PointSketch[0]
    Seeds: dict[str, Object] = {}
    CenterName = ""
    for Item in Features.FeatureItems:
        Identity = TextAction(Item.get("id"))
        if Identity == Plan.FeatureId:
            continue
        if Identity in CacheBySource:
            Seeds[Identity] = AddScaleSeedMut(
                Context, Geometry, Features, CacheBySource[Identity]
            )
        elif Identity == Plan.Center.FeatureId and Prep.PointSketch is not None:
            CenterName = AddScalePointMut(
                Context, Features, Plan.Center, *Prep.PointSketch, Item
            ).name
        else:
            TrackSketchMut(
                Features,
                Geometry,
                Sketches[TextAction(Item.get("sketch_id"))],
                Identity,
                Item,
            )
    if not CenterName and Prep.PointSketch is not None:
        CenterName = AddScalePointMut(
            Context, Features, Plan.Center, *Prep.PointSketch, None
        ).name
    Results = tuple(
        AddScaleResMut(
            Context,
            Features,
            Prep.Step,
            Seeds[Cache.Body.SourceId],
            Cache,
            Prep.Refs,
            Plan.Factors,
            Prep.Translation,
            CenterName,
            len(Prep.Bodies) == 1,
        )
        for Cache in Prep.Bodies
    )
    TrackScaleMut(Context, Features, Prep.Step, Results)
    Features.EditableScaleSteps = tuple(
        TextAction(Item.get("id")) for Item in Features.FeatureItems
    )
    return True
