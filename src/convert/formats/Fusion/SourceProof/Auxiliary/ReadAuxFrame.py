# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass, field as DataField

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive
from convert.formats.Fusion.ArchiveRead.ReadDesignPair import KDesignPrefix
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan

# auxiliary proof reads stay bounded independently from the general archive entry limit
KMaxAuxBytes = 8 * 1024 * 1024

# the same active asset contains the only auxiliary pair admitted by this proof
KActivePrefix = KDesignPrefix.removesuffix("FusionDesignSegmentType1/")


# a proof session can qualify semantic references without inflating its stream again
@MakeDataClass(frozen=True, slots=True)
class AuxFrame:
    BulkMember: ArchiveMember
    MetaMember: ArchiveMember
    Spans: tuple[RecordSpan, ...]
    BulkData: bytes = DataField(repr=False, compare=False)


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
    return AuxFrame(BulkMember, MetaMember, Spans, BulkData)
