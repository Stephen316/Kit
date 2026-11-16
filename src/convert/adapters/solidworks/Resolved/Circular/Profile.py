# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# Reach the region list through the witnessed circular sketch environment.
def ReadCircularEnvironment(Cursor):
    RequireArch(
        Cursor.ReadInts("<7H") == (0,) * 7, True, "unexpected post-display collections"
    )
    RequireArch(
        Cursor.ReadInts("<2Hi") == (2, 1, 2), True, "unsupported circular sketch state"
    )
    RequireArch(
        Cursor.ReadInts("<15i") == (4, 1, 2, *([1] * 10), 0, 1),
        True,
        "unexpected circular sketch environment fields",
    )
    RequireArch(
        Cursor.ReadInts("<4H") == (0,) * 4, True, "unexpected additional sketch arrays"
    )
    RequireArch(Cursor.ReadText() == "", True, "unexpected sketch line style label")
    RequireArch(
        Cursor.ReadValue("<Hf3i") == (65535, -1, -1, 1, -1),
        True,
        "unexpected sketch line settings",
    )
    RequireArch(
        Cursor.ReadPoint(3) == (0, 0, 0), True, "unexpected sketch presentation point"
    )
    (StateWord,) = Cursor.ReadInts("<I")
    RequireArch(
        Cursor.ReadInts("<2i") == (1, 0), True, "unexpected sketch presentation flags"
    )
    RequireArch(
        Cursor.ReadInts("<2H5i") == (0,) * 7, True, "unexpected pre-region collection"
    )
    return StateWord


# Prove that the closed region outline reaches the live circular member.
def ReadCircularRegion(Cursor, Circle):
    StateWord = ReadCircularEnvironment(Cursor)
    StartOffset = Cursor.Offset
    Cursor.TakePointer(("suObList",), KClassRefKind)
    RequireArch(Cursor.ReadInts("<H") == (1,), True, "expected one circular region")
    TakeShownClass(Cursor, "moSketchRegion_c")
    Region = Cursor.NextIndex - 1
    Cursor.TakePointer(("suObList",), KClassRefKind)
    RequireArch(
        Cursor.ReadInts("<H") == (1,), True, "expected one circular region outline"
    )
    _, _, Handle = Cursor.TakePointer(("sgArcHandle",), KClassRefKind)
    Cursor.ReadPayload("sgArcHandle", Handle)
    RequireArch(
        Cursor.Handles[Handle] == (Circle["arc_slot"], -1, 0),
        True,
        "the closed region outline does not select the circular member",
    )
    RequireArch(
        Cursor.ReadInts("<H7i") == (0,) * 8,
        True,
        "unexpected post-region sketch records",
    )
    return {
        "span": [StartOffset, Cursor.Offset],
        "object": Region,
        "outline_handle": Handle,
        "raw_environment_state": StateWord,
    }


# Tie the sole resolved profile edge to the native circle identity.
def ReadCircularChain(Cursor, Circle):
    StartOffset = Cursor.Offset
    RequireArch(
        Cursor.ReadInts("<Ii") == (1, 1),
        True,
        "expected one body-bearing profile chain",
    )
    _, _, Chain = Cursor.TakePointer(
        ("moSketchChain_c",), KDefinitionKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H") == (1,), True, "expected one circular chain edge")
    (Edge,) = Cursor.ReadInts("<I")
    RequireArch(
        Edge == Circle["native_id"],
        True,
        "chain edge does not name the native circular member",
    )
    RequireArch(
        Cursor.ReadInts("<H") == (1,), True, "unexpected secondary chain collection"
    )
    Cursor.ReadInts("<I6i")
    RequireArch(Cursor.ReadText() == "", True, "unexpected chain label")
    RequireArch(Cursor.ReadInts("<H") == (0,), True, "unexpected chain handle list")
    _, Pairs = Cursor.ReadInts("<2I")
    RequireArch(Pairs == 0, True, "unexpected chain pair map")
    Cursor.ReadNull()
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<3i") == (0, 0, 0), True, "unexpected circular chain return"
    )
    return {
        "span": [StartOffset, Cursor.Offset],
        "object": Chain,
        "edge_native_id": Edge,
    }


# Check that the right trim edge is owned by the same active profile and circle.
def ReadCircularTrim(Cursor, Profile, Circle):
    StartOffset = Cursor.Offset
    RequireArch(
        Cursor.ReadInts("<2H") == (0, 4), True, "unexpected circular profile flags"
    )
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<2i") == (-1, 0), True, "unexpected circular profile state"
    )
    (WireState,) = Cursor.ReadInts("<I")
    RequireArch(
        Cursor.ReadInts("<H") == (1,), True, "expected body-bearing circular contour"
    )
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<H") == (1,), True, "expected one circular trim surface"
    )
    Owner = {
        "profile_object": Profile["feature_node"],
        "native_feature_id": Profile["feature_id"],
    }
    Surface = ReadTrimSurface(Cursor, Owner)
    RequireArch(Cursor.ReadInts("<H") == (1,), True, "expected one circular trim edge")
    Edge = ReadContourEdge(Cursor, Owner, Surface)
    RequireArch(
        Edge["class"] == "moSegmRightTrimEdgeIdRep_c"
        and Edge["edge_id"] == Circle["native_id"],
        True,
        "trim edge does not name the circular member",
    )
    RequireArch(Cursor.ReadInts("<i") == (0,), True, "unexpected outer profile return")
    return {
        "span": [StartOffset, Cursor.Offset],
        "raw_state": WireState,
        "surface_object": Surface["object_index"],
        "same_file_object": Surface["file_reference"]["object_index"],
        "edge": Edge,
    }


# Prove the support and trim join before locating the following typed feature.
def ReadCircularProfileReturn(Cursor, Profile, Circle, Origin):
    Chain = ReadCircularChain(Cursor, Circle)
    StartOffset = Cursor.Offset
    Reference = ReadProfileRef(Cursor, KConfigGen)
    Datum = Origin.Support
    RequireArch(
        (Reference.FeatureId, Reference.AxisCode) == (Datum.FeatureId, Datum.AxisCode),
        True,
        "saved circular profile does not bind the typed Origin datum",
    )
    Normal = tuple(float(Axis == Datum.AxisCode) for Axis in (1, 2, 3))
    Axes = CheckProfileRef(Reference, Datum.ShiftScale[:3], Normal)
    Support = {
        "span": [StartOffset, Cursor.Offset],
        "feature": Reference.FeatureId,
        "axes": Axes,
    }
    Trim = ReadCircularTrim(Cursor, Profile, Circle)
    return {
        "chain": Chain,
        "support": Support,
        "trim": Trim,
        "next_record": ReadRectEnd(Cursor, True),
        "next_record_offset": Cursor.Offset,
    }
