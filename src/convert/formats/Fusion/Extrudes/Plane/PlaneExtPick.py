# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Extrudes.Plane.PlanePickSupport import (
    KProxySecondary,
    CheckPickLinks,
    ReadPickFooter,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.PlaneAxes import ReadPlaneAxes
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import KSelectProxy, SelectCursor
from convert.formats.Fusion.SelectionRef import (
    KSelectDesc,
    ReadEntityLeaf,
)
from interchange.geometry.models.Transform import Transform

# the selected plane context stores an independent local reference frame
KPlanePickContext = "CC54ECAD-6DE8-4DE1-803D-BBE0E751975B"

# the context link repeats the selected plane through a typed identity leaf
KPlanePickLink = "CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C"


# context and direct leaf must prove the same plane and component local frame
def ReadPlaneCtx(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ContextId: int,
    PlaneId: int,
    PlaneFrame: Transform,
) -> tuple[int, int]:
    Cursor = SelectCursor(BulkData, Owners, ContextId, KPlanePickContext)
    if (
        len(Cursor.DataValue) != 87
        or Cursor.TakeBytes(3) != bytes(3)
        or ReadPlaneAxes(Cursor.TakeBytes(72)) != PlaneFrame
        or Cursor.TakeBytes(1) != b"\1"
    ):
        raise ValueError("Fusion selected plane context frame disagrees")
    LinkId = ReadNativeRef(Cursor)
    LinkValue = SelectCursor(BulkData, Owners, LinkId, KPlanePickLink)
    if len(LinkValue.DataValue) != 14 or LinkValue.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion selected plane context identity link")
    LeafId = ReadNativeRef(LinkValue)
    if (
        LinkValue.TakeBytes(1) != bytes(1)
        or ReadEntityLeaf(BulkData, Owners, LeafId) != PlaneId
    ):
        raise ValueError("Fusion selected plane context and direct leaf disagree")
    return LinkId, LeafId


# selectors qualify both dependent records and the named construction feature
def CheckPlanePick(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ProxyId: int,
    SelectionIds: tuple[int, int, int],
    PlaneFeatureId: int,
    PlaneFrame: Transform,
) -> tuple[int, ...]:
    DescriptorId, LeafId, PlaneId = SelectionIds
    Proxy = SelectCursor(BulkData, Owners, ProxyId, KSelectProxy)
    if len(Proxy.DataValue) != 105 or Proxy.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion selected plane proxy")
    Proxy.Offset = 23
    SecondaryId = ReadNativeRef(Proxy)
    Secondary = SelectCursor(BulkData, Owners, SecondaryId, KProxySecondary)
    if Secondary.DataValue != b"\0\0\1\1\0":
        raise ValueError("Unsupported Fusion selected plane proxy secondary record")
    ProxyHelper, ProxySupport = ReadPickFooter(BulkData, Owners, Proxy)
    CheckPickLinks(BulkData, Owners, ProxySupport, ProxyId, (DescriptorId,))
    Descriptor = SelectCursor(BulkData, Owners, DescriptorId, KSelectDesc)
    Descriptor.Offset = 169
    if Descriptor.ReadLong() != 2 or Descriptor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion selected plane descriptor context count")
    ContextId = ReadNativeRef(Descriptor)
    LinkId, ContextLeaf = ReadPlaneCtx(BulkData, Owners, ContextId, PlaneId, PlaneFrame)
    DescHelper, DescSupport = ReadPickFooter(BulkData, Owners, Descriptor)
    CheckPickLinks(
        BulkData, Owners, DescSupport, DescriptorId, (PlaneFeatureId, DescriptorId)
    )
    return (
        ProxyId,
        DescriptorId,
        LeafId,
        SecondaryId,
        ProxyHelper,
        ProxySupport,
        ContextId,
        LinkId,
        ContextLeaf,
        DescHelper,
        DescSupport,
    )
