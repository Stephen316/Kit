# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# a selected limit must resolve within the same document scope as the profile frame
def GetPlaneInputs(
    StepValue: FeatureStep,
    SelectionId: str,
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Sketches: TypeMap[str, Sketch],
) -> tuple[SupportPlane, SupportPlane]:
    SketchValue = Sketches.get(StepValue.sketch_id or "")
    if not isinstance(SketchValue, Sketch) or SketchValue.id != StepValue.sketch_id:
        raise ValueError("plane extrusion requires a profile sketch")
    Profile = Frames.get(SketchValue.support_plane_id)
    if (
        not isinstance(Profile, SupportPlane)
        or Profile.id != SketchValue.support_plane_id
    ):
        raise ValueError("plane extrusion requires a profile sketch frame")
    PickValue = Selections.get(SelectionId)
    if (
        SelectionId not in StepValue.selection_ids
        or not isinstance(PickValue, Selection)
        or PickValue.id != SelectionId
        or len(PickValue.path) != 1
    ):
        raise ValueError(
            "plane extrusion requires a linked local support plane selection"
        )
    (Element,) = PickValue.path
    if (
        not isinstance(Element, SelectPathElem)
        or Element.entity_kind != "support_plane"
        or Element.subelement
    ):
        raise ValueError(
            "plane extrusion selection must directly identify a support plane"
        )
    Limit = Frames.get(Element.entity_id)
    if not isinstance(Limit, SupportPlane) or Limit.id != Element.entity_id:
        raise ValueError("plane extrusion selection references a missing support plane")
    return Profile, Limit
