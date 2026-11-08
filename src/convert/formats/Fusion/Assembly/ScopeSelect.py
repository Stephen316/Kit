# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping

from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch


# local selection targets must travel with the detached component geometry
def GetPickLinks(
    PickValue: Selection, Sketches: Mapping[str, Sketch]
) -> tuple[tuple[str, str], ...]:
    PathElems = PickValue.path
    if (
        not PathElems
        and PickValue.query.get("kind") == "component_origin_axis"
        and PickValue.query.get("axis") in ("X", "Y", "Z")
    ):
        return ()
    Kinds = tuple(Value.entity_kind for Value in PathElems)
    if Kinds == ("support_plane",):
        return (("plane", PathElems[0].entity_id),)
    if Kinds == ("sketch", "sketch_entity"):
        SketchValue = Sketches.get(PathElems[0].entity_id)
        if SketchValue is not None and any(
            Value.id == PathElems[1].entity_id for Value in SketchValue.entities
        ):
            return (("sketch", SketchValue.id),)
    raise ValueError(
        f"Fusion component selection {PickValue.id} has an unresolved local target"
    )
