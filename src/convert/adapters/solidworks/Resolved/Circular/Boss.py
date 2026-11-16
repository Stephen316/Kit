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
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.PlaneBasis import KSavedBasis, KSavedVector
from convert.adapters.solidworks.Resolved.Circular.Records import (
    CircularBoss,
    CircularExtent,
    ArcProfile,
)
from convert.adapters.solidworks.Resolved.OriginProfile import OriginProfile
from convert.adapters.solidworks.Sketch.CircularRecords import (
    CircularHeader,
    CircularMember,
    CircularPoint,
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


# convert an already bound local sketch point to the saved datum s world coordinates
def WorldPoint(
    PointValue: tuple[float, ...], SavedAxes: KSavedBasis, Origin: KSavedVector
) -> KSavedVector:
    XValue, YValue = PointValue
    First, Second, Third = (
        Offset + XValue * AxisX + YValue * AxisY
        for Offset, AxisX, AxisY in zip(Origin, *SavedAxes[:2], strict=True)
    )
    return First, Second, Third


# read the existing end distance parameter and start grammar through the resolved eof
def ReadBlindDepth(
    Cursor: ArchiveCursor, Centre: KSavedVector, Radius: float, Normal: KSavedVector
) -> CircularExtent:
    EndSpec = ReadEndHead(Cursor, KDefinitionKind, (0,))
    RequireArch(EndSpec["conditions"] == (0, 0), True, "expected circular blind end")
    TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        (TagValue.kind, TagValue.class_name, TagValue.schema)
        == (KDefinitionKind, "moDisplayDistanceDim_c", 1),
        True,
        "expected first circular boss distance display definition",
    )
    Depth, Reference = ReadDepthRefs(Cursor, DisplayKind=KDefinitionKind)
    Signed = SignedDistance(Depth, Reference, Normal)
    BaseValue = Reference["points_metres"][:3]
    RequireArch(
        Signed > 0
        and abs(PointOffset(BaseValue, Centre, Normal)) <= KPlaneTolerance
        and IsClose(
            Distance(BaseValue, Centre), Radius, rel_tol=0, abs_tol=KPlaneTolerance
        ),
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


# a circular boss must own the reached profile transfer and one side body chooser
def ReadRoundBoss(
    Cursor: ArchiveCursor,
    Profile: CircularHeader,
    ProfileReturn: ArcProfile,
    Circle: CircularMember,
    Points: list[CircularPoint],
    Origin: OriginProfile,
) -> CircularBoss:
    FileObject = ProfileReturn["trim"]["same_file_object"]
    Owner = ReadOpNode(
        Cursor,
        "moExtrusion_c",
        (0x40000140, 0xC0000140),
        Profile["feature_node"],
        FileObject,
    )
    Transfer, BodyValue = ReadScopeAtom(Cursor)
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
    SavedAxes = ProfileReturn["support"]["axes"]
    ShiftX, ShiftY, ShiftZ = Origin.Support.ShiftScale[:3]
    DatumOrigin = (ShiftX, ShiftY, ShiftZ)
    Centre = WorldPoint(Points[Circle["center_slot"]]["xy_m"], SavedAxes, DatumOrigin)
    Extent = ReadBlindDepth(Cursor, Centre, Circle["radial_metres"], SavedAxes[2])
    Depth = Extent["signed_depth_m"]
    First, Second, Third = (
        Value + Depth * AxisValue / 2
        for Value, AxisValue in zip(Centre, SavedAxes[2], strict=True)
    )
    Midpoint = (First, Second, Third)
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
        "saved_body_id": BodyValue,
        "choosers": Choices,
        "partition_object": Marker,
        "partition_state": StateValue,
        "atom_end": AtomEnd,
        "axis": SavedAxes[2],
        "start_center_m": Centre,
        "centroid_m": Midpoint,
    }
