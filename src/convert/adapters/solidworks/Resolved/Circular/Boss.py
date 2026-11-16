# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as Distance, isclose as IsClose

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
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.BossChooser import ReadBossChoices


# Convert an already bound local sketch point to the saved datum's world coordinates.
def WorldPoint(Xy, Axes, Origin):
    X, Y = Xy
    return tuple(
        Offset + X * AxisX + Y * AxisY
        for Offset, AxisX, AxisY in zip(Origin, *Axes[:2], strict=True)
    )


# Read the existing end, distance parameter and start grammar through the resolved EOF.
def ReadCircularExtent(Cursor, Centre, Radius, Normal):
    EndSpec = ReadEndHead(Cursor, KDefinitionKind, (0,))
    RequireArch(EndSpec["conditions"] == (0, 0), True, "expected circular blind end")
    Tag = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        (Tag.kind, Tag.class_name, Tag.schema)
        == (KDefinitionKind, "moDisplayDistanceDim_c", 1),
        True,
        "expected first circular boss distance display definition",
    )
    Depth, Reference = ReadDepthRefs(Cursor, DisplayKind=KDefinitionKind)
    Signed = SignedDistance(Depth, Reference, Normal)
    Base = Reference["points_metres"][:3]
    RequireArch(
        Signed > 0
        and abs(PointOffset(Base, Centre, Normal)) <= KPlaneTolerance
        and IsClose(Distance(Base, Centre), Radius, rel_tol=0, abs_tol=KPlaneTolerance),
        True,
        "circular boss depth does not run forward from its sketch perimeter",
    )
    StartOffset = ReadEndTail(Cursor, KDefinitionKind, 0)
    RequireArch(
        Cursor.ReadValue("<di") == (0, -1), True, "unexpected circular boss return"
    )
    EndOffset = Cursor.Offset
    RequireArch(
        Cursor.ReadInts("<i") == (0,) and Cursor.Offset == len(Cursor.BlobValue),
        True,
        "circular boss did not close the resolved stream",
    )
    return {
        "end_specification": EndSpec,
        "depth_display": Depth,
        "depth_reference": Reference,
        "signed_depth_m": Signed,
        "from_end_object": StartOffset,
        "boss_end": EndOffset,
        "stream_end": Cursor.Offset,
    }


# A circular boss must own the reached profile, transfer and one-side body chooser.
def ReadCircularBoss(Cursor, Profile, ProfileReturn, Circle, Points, Origin):
    FileObject = ProfileReturn["trim"]["same_file_object"]
    Owner = ReadOpNode(
        Cursor,
        "moExtrusion_c",
        (0x40000140, 0xC0000140),
        Profile["feature_node"],
        FileObject,
    )
    Transfer, Body = ReadScopeAtom(Cursor)
    Choices = ReadBossChoices(Cursor, Owner, EdgeIds=(Circle["native_id"],))
    RequireArch(
        Cursor.ReadInts("<H3i") == (0, 0, 0, 1),
        True,
        "unexpected circular partition selection",
    )
    _, _, Marker = Cursor.TakePointer(
        ("moPMarkRecord_c",), KClassRefKind, CompactOnly=True
    )
    (StateValue,) = Cursor.ReadInts("<i")
    ReadAtomMaps(Cursor)
    AtomEnd = Cursor.Offset
    ReadBodyReturn(Cursor)
    Axes = ProfileReturn["support"]["axes"]
    DatumOrigin = Origin.Support.ShiftScale[:3]
    Centre = WorldPoint(Points[Circle["center_slot"]]["xy_m"], Axes, DatumOrigin)
    Extent = ReadCircularExtent(Cursor, Centre, Circle["radial_metres"], Axes[2])
    Depth = Extent["signed_depth_m"]
    Midpoint = tuple(
        Value + Depth * Axis / 2 for Value, Axis in zip(Centre, Axes[2], strict=True)
    )
    RequireArch(
        Distance(Choices["centre"]["centre_and_scale"][:3], Midpoint)
        <= KPlaneTolerance,
        True,
        "circular boss chooser centre disagrees with the saved sketch and extent",
    )
    return {
        **Owner,
        **Extent,
        "transfer_object": Transfer,
        "saved_body_id": Body,
        "choosers": Choices,
        "partition_object": Marker,
        "partition_state": StateValue,
        "atom_end": AtomEnd,
        "axis": Axes[2],
        "start_center_m": Centre,
        "centroid_m": Midpoint,
    }
