# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
    ItemValue: Mapping[str, object],
) -> None:
    Sketch.properties.extend(
        (
            StringProp("KitFeatureId", Identity, Dynamic=True),
            IntegerProp("TimelineOrder", ItemValue.get("order", 0), Dynamic=True),
            JsonProp("SourceFeatureJSON", ItemValue),
        )
    )
    ReplaceNameMut(Sketch.properties, "Visibility", BoolProp("Visibility", False))
    Geometry.SketchObjects.remove(Sketch.name)
    Features.FeatureNames[Identity] = Sketch.name
    Features.FeatureObjects.append(Sketch.name)
