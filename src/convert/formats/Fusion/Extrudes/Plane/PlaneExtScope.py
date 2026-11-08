# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import CreatorScope
from convert.formats.Fusion.Extrudes.Plane.NativePlaneExt import NativePlaneExt
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane


# selected planes and source sketches must precede the feature in one native component
def CheckPlaneScope(
    StepValue: FeatureStep,
    FeatureId: int,
    PlaneStep: FeatureStep,
    Native: NativePlaneExt,
    FrameValue: SupportPlane,
    Steps: dict[str, FeatureStep],
    Scopes: dict[int, CreatorScope],
) -> None:
    SketchSteps = tuple(
        Source
        for Identity in StepValue.input_feature_ids
        if (Source := Steps.get(Identity)) is not None
        and Source.sketch_id == StepValue.sketch_id
        and Source.provenance is not None
        and Source.provenance.spans
        and Source.provenance.spans[0].record_kind == KSketchFeature
    )
    Scope = Scopes.get(FeatureId)
    if (
        len(SketchSteps) != 1
        or PlaneStep.order >= StepValue.order
        or Scope is None
        or Scope != Scopes.get(Native.PlaneFeatureId)
        or Scope.ComponentId != Native.ComponentId
        or FrameValue.attributes.get("fusion.component_object_id") != Native.ComponentId
    ):
        raise ValueError(
            "Fusion plane Extrude requires earlier inputs in the same component scope"
        )
    (SketchStep,) = SketchSteps
    if (
        SketchStep.provenance is None
        or SketchStep.order >= StepValue.order
        or Scope != Scopes.get(int(SketchStep.provenance.native_id))
    ):
        raise ValueError(
            "Fusion plane Extrude sketch scope differs from the selected plane"
        )
