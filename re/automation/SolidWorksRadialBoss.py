# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Read the reached terminal circular boss and its owned positive blind extent."""

from math import dist, isclose

from PairedCaptureIntake import require
from SolidWorksRadialChoices import read_radial_choices
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ReadTag,
)
from convert.adapters.solidworks.Resolved.BossDepth import ReadDepthRefs
from convert.adapters.solidworks.Resolved.BossEnd import ReadEndHead, ReadEndTail
from convert.adapters.solidworks.Resolved.BossEntry import ReadBodyReturn, ReadOpNode
from convert.adapters.solidworks.Resolved.PlaneAtom import ReadAtomMaps
from convert.adapters.solidworks.Resolved.Scope.Boss import ReadScopeAtom
from convert.adapters.solidworks.Resolved.Scope.Distance import (
    KPlaneTolerance,
    PointOffset,
    SignedDistance,
)


# Convert an already bound local sketch point to the saved datum's world coordinates.
def world_point(xy, axes, origin):
    x, y = xy
    return tuple(
        offset + x * axis_x + y * axis_y
        for offset, axis_x, axis_y in zip(origin, *axes[:2], strict=True)
    )


# Read the existing end, distance parameter and start grammar through the resolved EOF.
def read_radial_extent(cursor, centre, radius, normal):
    end_spec = ReadEndHead(cursor, KDefinitionKind, (0,))
    require(end_spec["conditions"] == (0, 0), "expected circular blind end")
    tag = ReadTag(cursor.BlobValue, cursor.Offset)
    require(
        (tag.kind, tag.class_name, tag.schema)
        == (KDefinitionKind, "moDisplayDistanceDim_c", 1),
        "expected first circular boss distance display definition",
    )
    depth, reference = ReadDepthRefs(cursor, DisplayKind=KDefinitionKind)
    signed = SignedDistance(depth, reference, normal)
    base = reference["points_metres"][:3]
    require(
        signed > 0
        and abs(PointOffset(base, centre, normal)) <= KPlaneTolerance
        and isclose(dist(base, centre), radius, rel_tol=0, abs_tol=KPlaneTolerance),
        "circular boss depth does not run forward from its sketch perimeter",
    )
    start = ReadEndTail(cursor, KDefinitionKind, 0)
    require(cursor.ReadValue("<di") == (0, -1), "unexpected circular boss return")
    end = cursor.Offset
    require(
        cursor.ReadInts("<i") == (0,) and cursor.Offset == len(cursor.BlobValue),
        "circular boss did not close the resolved stream",
    )
    return {
        "end_specification": end_spec,
        "depth_display": depth,
        "depth_reference": reference,
        "signed_depth_m": signed,
        "from_end_object": start,
        "boss_end": end,
        "stream_end": cursor.Offset,
    }


# A circular boss must own the reached profile, transfer and one-side body chooser.
def read_radial_boss(cursor, profile, profile_return, circle, points, origin):
    file_object = profile_return["trim"]["same_file_object"]
    owner = ReadOpNode(
        cursor,
        "moExtrusion_c",
        (0x40000140, 0xC0000140),
        profile["feature_node"],
        file_object,
    )
    transfer, body = ReadScopeAtom(cursor)
    choices = read_radial_choices(cursor, owner, circle["native_id"])
    require(
        cursor.ReadInts("<H3i") == (0, 0, 0, 1),
        "unexpected circular partition selection",
    )
    _, _, marker = cursor.TakePointer(
        ("moPMarkRecord_c",), KClassRefKind, CompactOnly=True
    )
    (state,) = cursor.ReadInts("<i")
    ReadAtomMaps(cursor)
    atom_end = cursor.Offset
    ReadBodyReturn(cursor)
    axes = profile_return["support"]["axes"]
    datum_origin = origin.Support.ShiftScale[:3]
    centre = world_point(points[circle["center_slot"]]["xy_m"], axes, datum_origin)
    extent = read_radial_extent(cursor, centre, circle["radial_metres"], axes[2])
    depth = extent["signed_depth_m"]
    midpoint = tuple(
        value + depth * axis / 2 for value, axis in zip(centre, axes[2], strict=True)
    )
    require(
        dist(choices["centre"]["centre_and_scale"][:3], midpoint) <= KPlaneTolerance,
        "circular boss chooser centre disagrees with the saved sketch and extent",
    )
    return {
        **owner,
        **extent,
        "transfer_object": transfer,
        "saved_body_id": body,
        "choosers": choices,
        "partition_object": marker,
        "partition_state": state,
        "atom_end": atom_end,
        "axis": axes[2],
        "start_center_m": centre,
        "centroid_m": midpoint,
    }


# Cross-check the reached profile, boss, direction and driving depth with the licensed reader.
def check_licensed_boss(boss, native):
    depth = boss["depth_display"]["dimension"]
    native_feature = native["feature"]
    native_dimension = native["depth_dimension"]
    require(
        (native_feature["name"], native_feature["id"])
        == (boss["name"], boss["native_feature_id"])
        and native_feature["type"] == "Extrusion"
        and native_feature["suppressed"] is False
        and native["end_condition"] == 0
        and native["reverse_direction"] is native["both_directions"] is False
        and native_dimension["owner"] == native_feature
        and native_dimension["driven_state"] == 2
        and native_dimension["name"] == depth["parameter_name"]
        and isclose(
            native["depth_m"],
            boss["signed_depth_m"],
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        )
        and isclose(
            native_dimension["system_value_m"],
            depth["metres"],
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        ),
        "licensed circular boss ownership or driving depth disagrees with the archive",
    )
