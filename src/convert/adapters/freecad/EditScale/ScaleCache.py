# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
    Plan: ScaleBodyPlan,
    Translation: SpaceVector,
) -> ScaleCache | None:
    Sketch = EditProfile(Context, Geometry, Feature, Plan.SketchId)
    DepthRef = Context.Parameters.expression(Plan.DepthId)
    if Sketch is None or not DepthRef:
        return None
    Source = BrepModelBrep(Plan.SourceModel)
    Result = BrepModelBrep(Plan.ResultModel, RootTranslation=Translation)
    if not Source or not Result:
        return None
    return ScaleCache(Plan, Feature, Sketch, DepthRef, Source, Result)
