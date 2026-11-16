# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Prove the region, circular profile, and following boss boundary."""

from PairedCaptureIntake import require
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Resolved.ContourSurf import (
    ReadContourEdge,
    ReadTrimSurface,
)
from convert.adapters.solidworks.Resolved.ContourTrim import ReadRectEnd
from convert.adapters.solidworks.Resolved.ProfilePlane import (
    CheckProfileRef,
    ReadProfileRef,
)
from convert.adapters.solidworks.Sketch.Displays import TakeShownClass


# Reach the region list through the witnessed circular sketch environment.
def read_circular_environment(cursor):
    require(cursor.ReadInts("<7H") == (0,) * 7, "unexpected post-display collections")
    require(cursor.ReadInts("<2Hi") == (2, 1, 2), "unsupported circular sketch state")
    require(
        cursor.ReadInts("<15i") == (4, 1, 2, *([1] * 10), 0, 1),
        "unexpected circular sketch environment fields",
    )
    require(cursor.ReadInts("<4H") == (0,) * 4, "unexpected additional sketch arrays")
    require(cursor.ReadText() == "", "unexpected sketch line style label")
    require(
        cursor.ReadValue("<Hf3i") == (65535, -1, -1, 1, -1),
        "unexpected sketch line settings",
    )
    require(cursor.ReadPoint(3) == (0, 0, 0), "unexpected sketch presentation point")
    (state_word,) = cursor.ReadInts("<I")
    require(cursor.ReadInts("<2i") == (1, 0), "unexpected sketch presentation flags")
    require(cursor.ReadInts("<2H5i") == (0,) * 7, "unexpected pre-region collection")
    return state_word


# Prove that the closed region outline reaches the live circular member.
def read_circular_region(cursor, circle):
    state_word = read_circular_environment(cursor)
    start = cursor.Offset
    cursor.TakePointer(("suObList",), KClassRefKind)
    require(cursor.ReadInts("<H") == (1,), "expected one circular region")
    TakeShownClass(cursor, "moSketchRegion_c")
    region = cursor.NextIndex - 1
    cursor.TakePointer(("suObList",), KClassRefKind)
    require(cursor.ReadInts("<H") == (1,), "expected one circular region outline")
    _, _, handle = cursor.TakePointer(("sgArcHandle",), KClassRefKind)
    cursor.ReadPayload("sgArcHandle", handle)
    require(
        cursor.Handles[handle] == (circle["arc_slot"], -1, 0),
        "the closed region outline does not select the circular member",
    )
    require(
        cursor.ReadInts("<H7i") == (0,) * 8, "unexpected post-region sketch records"
    )
    return {
        "span": [start, cursor.Offset],
        "object": region,
        "outline_handle": handle,
        "raw_environment_state": state_word,
    }


# Tie the sole resolved profile edge to the native circle identity.
def read_circular_chain(cursor, circle):
    start = cursor.Offset
    require(cursor.ReadInts("<Ii") == (1, 1), "expected one body-bearing profile chain")
    _, _, chain = cursor.TakePointer(
        ("moSketchChain_c",), KDefinitionKind, CompactOnly=True
    )
    require(cursor.ReadInts("<H") == (1,), "expected one circular chain edge")
    (edge,) = cursor.ReadInts("<I")
    require(
        edge == circle["native_id"],
        "chain edge does not name the native circular member",
    )
    require(cursor.ReadInts("<H") == (1,), "unexpected secondary chain collection")
    cursor.ReadInts("<I6i")
    require(cursor.ReadText() == "", "unexpected chain label")
    require(cursor.ReadInts("<H") == (0,), "unexpected chain handle list")
    _, pairs = cursor.ReadInts("<2I")
    require(pairs == 0, "unexpected chain pair map")
    cursor.ReadNull()
    cursor.ReadNull()
    require(cursor.ReadInts("<3i") == (0, 0, 0), "unexpected circular chain return")
    return {"span": [start, cursor.Offset], "object": chain, "edge_native_id": edge}


# Check that the right trim edge is owned by the same active profile and circle.
def read_circular_trim(cursor, profile, circle):
    start = cursor.Offset
    require(cursor.ReadInts("<2H") == (0, 4), "unexpected circular profile flags")
    cursor.ReadNull()
    require(cursor.ReadInts("<2i") == (-1, 0), "unexpected circular profile state")
    (wire_state,) = cursor.ReadInts("<I")
    require(cursor.ReadInts("<H") == (1,), "expected body-bearing circular contour")
    cursor.ReadNull()
    require(cursor.ReadInts("<H") == (1,), "expected one circular trim surface")
    owner = {
        "profile_object": profile["feature_node"],
        "native_feature_id": profile["feature_id"],
    }
    surface = ReadTrimSurface(cursor, owner)
    require(cursor.ReadInts("<H") == (1,), "expected one circular trim edge")
    edge = ReadContourEdge(cursor, owner, surface)
    require(
        edge["class"] == "moSegmRightTrimEdgeIdRep_c"
        and edge["edge_id"] == circle["native_id"],
        "trim edge does not name the circular member",
    )
    require(cursor.ReadInts("<i") == (0,), "unexpected outer profile return")
    return {
        "span": [start, cursor.Offset],
        "raw_state": wire_state,
        "surface_object": surface["object_index"],
        "same_file_object": surface["file_reference"]["object_index"],
        "edge": edge,
    }


# Prove the support and trim join before locating the following typed feature.
def read_profile_return(cursor, profile, circle, origin):
    chain = read_circular_chain(cursor, circle)
    start = cursor.Offset
    reference = ReadProfileRef(cursor, KConfigGen)
    datum = origin.Support
    require(
        (reference.FeatureId, reference.AxisCode) == (datum.FeatureId, datum.AxisCode),
        "saved circular profile does not bind the typed Origin datum",
    )
    normal = tuple(float(axis == datum.AxisCode) for axis in (1, 2, 3))
    axes = CheckProfileRef(reference, datum.ShiftScale[:3], normal)
    support = {
        "span": [start, cursor.Offset],
        "feature": reference.FeatureId,
        "axes": axes,
    }
    trim = read_circular_trim(cursor, profile, circle)
    return {
        "chain": chain,
        "support": support,
        "trim": trim,
        "next_record": ReadRectEnd(cursor, True),
        "next_record_offset": cursor.Offset,
    }
