# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Bound the reached diameter display before returning to its sketch."""

from math import isclose

from PairedCaptureIntake import require
from convert.adapters.solidworks.Sketch.DimHandle import ReadDimHandle
from convert.adapters.solidworks.Sketch.DisplayFields import (
    ReadCache,
    ReadEmptyTexts,
    ReadNulls,
)
from convert.adapters.solidworks.Sketch.Displays import TakeShownClass


# Connect the displayed radial handle to the active sketch and its sole driving value.
def read_radial_handle(cursor, sketch_node):
    cursor.ReadNull()
    style = cursor.ReadValue("<d2ihf2ihf8ihf5i")
    require(style[-5:] == (0, 0, 0, 0, 4), "unexpected radial visual mode")
    require(cursor.ReadPoint(12) == (0,) * 12, "unexpected radial position array")
    require(cursor.ReadInts("<i") == (2,), "unexpected radial display direction count")
    cursor.ReadPoint(6)
    ReadEmptyTexts(cursor, 1)
    text_point = cursor.ReadPoint(3)
    require(cursor.ReadInts("<i") == (17,), "expected radial display wire kind")
    cursor.ReadNull()
    settings = cursor.ReadValue("<i4d4i2diH3id2i")
    require(
        settings[11:16] == (0, 0, 0, 0, 0) and settings[-2:] == (0, 1),
        "unexpected radial display handle route",
    )
    start = cursor.Offset
    TakeShownClass(cursor, "moSkDimHandleRadial_c")
    handle = cursor.NextIndex - 1
    slot = ReadDimHandle(cursor, sketch_node)
    require(slot == 0, "radial display does not reach the sole G1 value")
    return {
        "span": [start, cursor.Offset],
        "object": handle,
        "sketch_object": sketch_node,
        "g1_slot": slot,
        "text_point_m": text_point,
    }


# Confirm that both measured display caches describe the owned diameter.
def read_value_caches(cursor, diameter):
    require(cursor.ReadInts("<3H") == (0, 0, 0), "unexpected radial display groups")
    require(cursor.ReadText() == "<MOD-DIAM>", "missing saved diameter label")
    ReadEmptyTexts(cursor, 3)
    cursor.ReadPoint(22)
    cursor.ReadInts("<i7H")
    cursor.ReadPoint(3)
    copies = ReadCache(cursor)
    require(
        all(isclose(value, diameter, rel_tol=0, abs_tol=1e-9) for value in copies),
        "saved radial display caches disagree with the driving value",
    )
    return copies


# Reach the subtype-specific return through the framed common display fields.
def read_common_return(cursor):
    TakeShownClass(cursor, "moFavoriteHandle_c")
    appearance = cursor.ReadValue("<2iId2HI4didHi30Id")
    require(
        appearance[:6] == (0, -1, 0, -1, 1, 1), "unexpected radial display favorite"
    )
    ReadEmptyTexts(cursor, 4)
    cursor.ReadInts("<2HiI")
    ReadNulls(cursor, 3)
    require(cursor.ReadInts("<I") == (1002101,), "unexpected radial display flags")
    ReadNulls(cursor, 2)
    require(cursor.ReadInts("<3i") == (0, 0, 0), "unexpected additional display items")
    cursor.ReadNull()
    cursor.ReadValue("<5id6i")
    ReadEmptyTexts(cursor, 2)
    cursor.ReadInts("<3i")
    ReadEmptyTexts(cursor, 1)
    cursor.ReadValue("<2i3d2i")
    ReadEmptyTexts(cursor, 1)


# Recognize the witnessed radial return and leave the appearance flags uninterpreted.
def read_radial_suffix(cursor):
    start = cursor.Offset
    (flags,) = cursor.ReadInts("<i")
    require(cursor.ReadPoint(12) == (0,) * 12, "unexpected auxiliary radial placement")
    require(cursor.ReadInts("<i") == (0,), "unexpected radial label collection")
    cursor.ReadNull()
    ReadEmptyTexts(cursor, 1)
    cursor.ReadNull()
    require(cursor.ReadInts("<i") == (0,), "unexpected auxiliary radial transform")
    cursor.ReadNull()
    require(cursor.ReadInts("<i") == (0,), "unexpected radial helper flags")
    cursor.ReadNull()
    require(cursor.ReadInts("<i") == (0,), "unexpected radial display return")
    return {"span": [start, cursor.Offset], "raw_flags": flags}


# Continue from the common display object to the circular sketch environment.
def read_display_return(cursor, profile, diameter):
    handle = read_radial_handle(cursor, profile["sketch_node"])
    copy_values = read_value_caches(cursor, diameter["diameter_m"])
    read_common_return(cursor)
    suffix = read_radial_suffix(cursor)
    return {"handle": handle, "diameter_cache_m": copy_values, "radial_suffix": suffix}
