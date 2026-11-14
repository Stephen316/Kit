from typing import cast as CastValue

from convert.formats.Fusion.AssetCodec.Zip.ZipLimits import KMaxMemberBytes
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


def CheckStreams(Value: SegmentStreams, SlotValue: SegmentSlot) -> None:
    if (
        not isinstance(CastValue(object, Value), SegmentStreams)
        or type(Value.SegmentId) is not int
        or Value.SegmentId != SlotValue.SegmentId
        or type(Value.Metadata) is not bytes
        or type(Value.BulkData) is not bytes
        or not 0 < len(Value.Metadata) <= KMaxMemberBytes
        or not 0 < len(Value.BulkData) <= KMaxMemberBytes
    ):
        raise ValueError("Invalid Fusion container segment streams")
    Metadata = ReadMetaWire(Value.Metadata, Segment=SlotValue.Segment)
    if Metadata.Header.SegmentId != SlotValue.SegmentId:
        raise ValueError("Fusion manifest and segment identity disagree")
    Primary = sorted(Metadata.Primary, key=lambda Entry: Entry.ObjectId)
    if any(
        Earlier.Offset >= Later.Offset for Earlier, Later in zip(Primary, Primary[1:])
    ):
        raise ValueError("Fusion primary offsets must increase in identity order")
    Owners = {Entry.ObjectId for Entry in Primary}
    if len(set(Metadata.StoredIds)) != len(Metadata.StoredIds) or not set(
        Metadata.StoredIds
    ).issubset(Owners):
        raise ValueError("Fusion segment roots disagree with primary identities")
    _ = ReadBulkSpans(Value.BulkData, Value.Metadata, Segment=SlotValue.Segment)
