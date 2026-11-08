# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.Archive import (
    AddBrepEntryMut,
    AddExtToolMut,
    BoolProp,
    DocContext,
    DocFeatures,
    DocGeometry,
    ExpressionProp,
    Object,
    ReplaceNameMut,
    SetProfRulesMut,
    ShapeProp,
    TrackSolidMut,
)
from convert.adapters.freecad.EditBodyRev.BodyRevExpr import BodyDepthDir
from convert.adapters.freecad.EditScale.ScaleCache import ScaleCache


# hidden upstream extrusions retain the native profile and independently writable depth
def AddScaleSeedMut(
    Context: DocContext, Geometry: DocGeometry, Features: DocFeatures, Cache: ScaleCache
) -> Object:
    Axis = (0.0, 0.0, 1.0)
    Seed = AddExtToolMut(
        Context, Cache.Feature, Axis, Cache.Body.Depth, 0.0, False, Cache.DepthRef
    )
    ReplaceNameMut(
        Seed.properties,
        "ExpressionEngine",
        ExpressionProp(
            [
                ("Dir", BodyDepthDir(Axis, Cache.DepthRef, Cache.Sketch.name)),
                ("LengthFwd", Cache.DepthRef),
            ]
        ),
    )
    Entry = AddBrepEntryMut(Features.PayloadEntries, Seed.name, Cache.SourceBrep)
    ReplaceNameMut(Seed.properties, "Shape", ShapeProp(Entry))
    ReplaceNameMut(Seed.properties, "Visibility", BoolProp("Visibility", False))
    ReplaceNameMut(Cache.Sketch.properties, "Visibility", BoolProp("Visibility", False))
    SetProfRulesMut(Context, Geometry, Cache.Sketch, Cache.Body.SketchId)
    TrackSolidMut(Features, Cache.Feature, Seed)
    return Seed
