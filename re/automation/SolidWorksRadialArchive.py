# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Read the witnessed circular boss sketch prefix using the SDK archive cursor."""

from math import dist, isclose

from PairedCaptureIntake import require, sha256
from SolidWorksRadialDisplay import read_display_return
from SolidWorksRadialProfile import read_circular_region, read_profile_return
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import (
    ContainerMo,
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.DimFields import ReadDimFields
from convert.adapters.solidworks.Sketch.DisplayOpen import ReadDisplayBase
from convert.adapters.solidworks.Sketch.Displays import TakeShownClass
from convert.adapters.solidworks.Sketch.Members import (
    ReadMember,
    ReadPointMut,
    ReadPointSlot,
)
from convert.adapters.solidworks.Sketch.Relations import ReadRelations
from convert.adapters.solidworks.Sketch.SketchTail import ReadLogicalTail

CONFIG = "Contents/Config-0"
RESOLVED = f"{CONFIG}-ResolvedFeatures"
CIRCLE_HANDLE = "sgArcHandle"


class RadialCursor(SketchArchive):
    """Limit otherwise shared point adjacency to a witnessed circular handle."""

    def ReadObject(self, *expected):
        if expected == (None, "sgLineHandle"):
            expected = (None, CIRCLE_HANDLE)
        return super().ReadObject(*expected)

    def ReadPayload(self, name, index):
        if name == CIRCLE_HANDLE:
            (slot,) = self.ReadInts("<H")
            require(slot < 0x777F, "unsupported circular handle index width")
            owner, flags = self.ReadInts("<2i")
        elif name == "sgEntHandle":
            require(
                self.ReadInts("<H") == (0x777F,),
                "expected invalid placeholder index width",
            )
            slot, owner, flags = self.ReadInts("<3i")
            require(slot == -2, "unexpected second G1 operand")
        else:
            super().ReadPayload(name, index)
            return
        require((owner, flags) == (-1, 0), "circular handle is not local")
        self.Handles[index] = slot, owner, flags


def open_profile(data):
    archive = SldprtArchive.from_bytes(data)
    generation = ContainerMo(archive.streams)
    config = archive.require(CONFIG)
    resolved = archive.require(RESOLVED)
    config_map, config_walk = ReadOrdinaryMap(config, generation)
    require(
        config_walk["atom_count"] == 1 and sum(map(len, config_walk["regions"])) == 1,
        "expected one archived body atom and region",
    )
    parent = OpenResolved(resolved, config_map, 19)
    system = ReadSysPrefix(parent)
    origin = ReadOrigin(parent, generation)
    require(
        origin.Support.FeatureId == system.Planes[0].FeatureId,
        "typed origin datum differs",
    )
    profile_start = parent.Offset
    _, _, feature_node = parent.TakePointer(("moProfileFeature_c",), KDefinitionKind)
    parent.TakePointer(("moNodeName_c",), KClassRefKind)
    name, feature_id, _ = ReadProfileHead(parent, (0x40000000, 0xC0000000))
    _, _, sketch_node = parent.TakePointer(("sgSketch",), KClassRefKind)
    identity = {
        "name": name,
        "feature_id": feature_id,
        "feature_node": feature_node,
        "feature_start": profile_start,
        "sketch_node": sketch_node,
    }
    return RadialCursor(parent), identity, origin


def read_points(cursor):
    require(cursor.ReadCount() == 3, "expected center, seam and origin-proxy points")
    points = []
    for slot in range(3):
        start = cursor.Offset
        earlier = set(cursor.Handles)
        identity, references, coords = ReadPointMut(cursor)
        adjacency = [
            handle
            for handle in cursor.Handles.keys() - earlier
            if cursor.Objects[handle] == CIRCLE_HANDLE
        ]
        points.append(
            {
                "slot": slot,
                "id": identity,
                "span": [start, cursor.Offset],
                "references": references,
                "xy_m": coords,
                "arc_adjacency": sorted(adjacency),
            }
        )
    require(
        len({row["id"] for row in points}) == len(points),
        "duplicate source point identity",
    )
    return points


def read_circle(cursor, points):
    require(
        cursor.ReadInts("<4i") == (0, 0, 0, 1),
        "expected one arc and no other primary members",
    )
    start = cursor.Offset
    require(cursor.ReadInts("<H") == (0,), "unsupported circular member mode")
    _, identity, flags, flags_two, references, external = ReadMember(cursor)
    seam, end = ReadPointSlot(cursor), ReadPointSlot(cursor)
    require(cursor.ReadInts("<2H") == (1, 0), "unsupported circular endpoint fields")
    require(cursor.ReadPoint(1) == (-1,), "unsupported arc tolerance state")
    (orientation,) = cursor.ReadInts("<i")
    center = ReadPointSlot(cursor)
    require(cursor.ReadInts("<4i") == (-2,) * 4, "unsupported arc auxiliary references")
    require(
        (flags, flags_two, references, external, orientation) == (4, 0, 1, 0, 1)
        and seam == end
        and seam != center
        and {seam, center} <= set(range(len(points))),
        "expected one ordinary positive full circle",
    )
    adjacency = points[seam]["arc_adjacency"]
    require(
        len(adjacency) == 1
        and cursor.Handles[adjacency[0]] == (0, -1, 0)
        and all(
            not point["arc_adjacency"] for point in points if point["slot"] != seam
        ),
        "the seam does not own the local circular adjacency",
    )
    radius = dist(points[seam]["xy_m"], points[center]["xy_m"])
    require(radius > 0, "circle center and seam coincide")
    return {
        "span": [start, cursor.Offset],
        "arc_slot": 0,
        "native_id": identity,
        "seam_slot": seam,
        "center_slot": center,
        "orientation": orientation,
        "radial_metres": radius,
        "adjacency_handle": adjacency[0],
    }


def read_diameter(cursor, circle):
    require(cursor.ReadInts("<8i") == (0,) * 8, "unexpected remaining geometry groups")
    require(cursor.ReadInts("<H") == (1,), "expected one radial G1 value")
    start = cursor.Offset
    _, _, object_index = cursor.TakePointer(("sgCircleDim",))
    dim_id, scalar, state = ReadDimFields(cursor, "moLengthParameter_c")
    require(
        state == 0 and cursor.ReadInts("<i4H") == (15, 2, 0, 0, 0),
        "unsupported G1 diameter state",
    )
    arc_handle = cursor.ReadObject(CIRCLE_HANDLE)
    placeholder = cursor.ReadObject("sgEntHandle")
    require(
        cursor.Handles[arc_handle] == (circle["arc_slot"], -1, 0)
        and cursor.Handles[placeholder] == (-2, -1, 0),
        "the active diameter does not bind its one circular operand",
    )
    require(
        cursor.ReadInts("<2i") == (0, 0) and cursor.ReadPoint(3) == (1, 0, 0),
        "unsupported radial value return",
    )
    name, value = cursor.Scalars[scalar]
    require(
        isclose(value, 2 * circle["radial_metres"], rel_tol=0, abs_tol=1e-9),
        "radial value and geometry disagree",
    )
    return {
        "span": [start, cursor.Offset],
        "native_id": dim_id,
        "object": object_index,
        "parameter_object": scalar,
        "parameter_offset": cursor.ScalarOffsets[scalar],
        "parameter_name": name,
        "diameter_m": value,
        "arc_handle": arc_handle,
        "invalid_second_handle": placeholder,
    }


def read_origin_join(cursor, points, circle, origin):
    require(
        cursor.ReadInts("<H") == (0,) and not ReadRelations(cursor),
        "unexpected other value or logical dimensions",
    )
    (coincident,) = ReadLogicalTail(
        cursor, [(row["slot"], row["id"]) for row in points]
    )
    center = circle["center_slot"]
    (proxy,) = set(range(len(points))) - {center, circle["seam_slot"]}
    reference = cursor.PointReferences.get(points[proxy]["id"])
    require(
        not coincident["deleted"]
        and not coincident["suppressed"]
        and set(coincident["point_indices"]) == {center, proxy}
        and set(cursor.PointReferences) == {points[proxy]["id"]}
        and reference is not None
        and reference["feature_id"] == origin.FeatureId
        and reference["handle_class"] == "sgPointHandle"
        and reference["handle_fields"] == (0, -1, 0)
        and points[center]["xy_m"]
        == points[proxy]["xy_m"]
        == origin.Geometry.PointValue,
        "active G2 does not join the actual circle center to the typed Origin point",
    )
    return {**coincident, "origin_feature": origin.FeatureId, "origin_proxy": reference}


def read_display_prefix(cursor):
    start = cursor.Offset
    TakeShownClass(cursor, "suObList")
    require(cursor.ReadInts("<H") == (1,), "expected one radial display")
    display_start = cursor.Offset
    _, _, display = cursor.TakePointer(("moDisplayRadialDim_c",))
    ReadDisplayBase(cursor, True)
    return {
        "list_start": start,
        "display_start": display_start,
        "display_object": display,
        "common_prefix_end": cursor.Offset,
    }


# Continue through the radial display and profile only for the explicit research mode.
def inspect_archive(data, profile_return=False):
    cursor, profile, origin = open_profile(data)
    points = read_points(cursor)
    circle = read_circle(cursor, points)
    diameter = read_diameter(cursor, circle)
    coincidence = read_origin_join(cursor, points, circle, origin)
    display = read_display_prefix(cursor)
    result = {
        "resolved_stream": RESOLVED,
        "resolved_sha256": sha256(cursor.BlobValue),
        "profile": profile,
        "points": points,
        "circle": circle,
        "diameter": diameter,
        "coincidence": coincidence,
        "display_prefix": display,
        "unresolved": [
            "radial_display_owner_and_value_slot",
            "circular_region_and_profile_return",
            "complete_resolved_boss_graph",
        ],
    }
    if profile_return:
        result["display_return"] = read_display_return(cursor, profile, diameter)
        result["region"] = read_circular_region(cursor, circle)
        result["profile_return"] = read_profile_return(cursor, profile, circle, origin)
        result["unresolved"] = ["complete_resolved_boss_graph"]
    return result
