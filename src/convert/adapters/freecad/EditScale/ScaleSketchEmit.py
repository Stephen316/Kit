# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping

from convert.adapters.freecad.Archive import (
    BoolProp,
    DocFeatures,
    DocGeometry,
    IntegerProp,
    JsonProp,
    Object,
    ReplaceNameMut,
    StringProp,
)


# a source sketch step stays on the real sketch without a second group owner
def TrackSketchMut(
    Features: DocFeatures,
    Geometry: DocGeometry,
    Sketch: Object,
    Identity: str,
    Item: Mapping[str, object],
) -> None:
    Sketch.properties.extend(
        (
            StringProp("KitFeatureId", Identity, Dynamic=True),
            IntegerProp("TimelineOrder", Item.get("order", 0), Dynamic=True),
            JsonProp("SourceFeatureJSON", Item),
        )
    )
    ReplaceNameMut(Sketch.properties, "Visibility", BoolProp("Visibility", False))
    Geometry.SketchObjects.remove(Sketch.name)
    Features.FeatureNames[Identity] = Sketch.name
    Features.FeatureObjects.append(Sketch.name)
