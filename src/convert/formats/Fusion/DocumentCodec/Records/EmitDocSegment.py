from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.Records.SlackLimit import (
    KMaxDesignSlack,
    KSlackKinds,
)
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment


def EmitDocSegment(Value: ParsedSegment) -> SegmentStreams:
    if type(Value.BulkSlack) is not bytes:
        raise ValueError("Fusion bulk slack must be bytes")
    KindValue = Value.Metadata.Header.Segment
    if Value.BulkSlack and KindValue not in KSlackKinds:
        raise ValueError(
            "Only the Fusion ACT, Design and Browser bulk streams carry slack"
        )
    if KindValue is SegmentKind.KDesign and len(Value.BulkSlack) > KMaxDesignSlack:
        raise ValueError("Fusion Design bulk slack exceeds its limit")
    Records = EncodeEntities(Value.Records, Value.Metadata.Classes, Value.Profile)
    BulkData, MetaData = EmitSegment(Value.Metadata, Records)
    return SegmentStreams(
        Value.Metadata.Header.SegmentId, MetaData, BulkData + Value.BulkSlack
    )
