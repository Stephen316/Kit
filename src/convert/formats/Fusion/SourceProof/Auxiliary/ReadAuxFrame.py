# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    IndexedArchive,
    KDesignPrefix,
)
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan

# auxiliary proof reads stay bounded independently from the general archive entry limit
KMaxAuxBytes = 8 * 1024 * 1024

# the same active asset contains the only auxiliary pair admitted by this proof
KActivePrefix = KDesignPrefix.removesuffix("FusionDesignSegmentType1/")


# immutable structural evidence carries record identities without retaining inflated buffers
@MakeDataClass(frozen=True, slots=True)
class AuxFrame:
    BulkMember: ArchiveMember
    MetaMember: ArchiveMember
    Spans: tuple[RecordSpan, ...]


# both exact stream members must agree on framing before any claims are published
def ReadAuxFrame(Archive: IndexedArchive, Segment: SegmentKind) -> AuxFrame:
    if Segment is not SegmentKind.KBrowser and Segment is not SegmentKind.KAct:
        raise ValueError("Unsupported Fusion auxiliary segment kind")
    Prefix = f"{KActivePrefix}{Segment.value}1/"
    Members = {Value.Name: Value for Value in Archive.Members}
    BulkMember = Members.get(Prefix + "BulkStream.dat")
    MetaMember = Members.get(Prefix + "MetaStream.dat")
    if (
        BulkMember is None
        or MetaMember is None
        or any(
            Value.IsDirectory or not 0 < Value.Size <= KMaxAuxBytes
            for Value in (BulkMember, MetaMember)
        )
    ):
        raise ValueError("Missing or oversized Fusion auxiliary stream pair")
    MetaData = Archive.ReadMember(MetaMember.Name, KMaxAuxBytes)
    BulkData = Archive.ReadMember(BulkMember.Name, KMaxAuxBytes)
    Spans = ReadBulkSpans(BulkData, MetaData, Segment=Segment)
    return AuxFrame(BulkMember, MetaMember, Spans)
