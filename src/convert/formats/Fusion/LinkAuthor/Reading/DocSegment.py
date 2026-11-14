from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MetaIndex import SegmentKind


def SegmentOf(Model: DocumentModel, KindValue: SegmentKind) -> ParsedSegment:
    Found = tuple(
        Segment
        for Segment in Model.Segments
        if Segment.Metadata.Header.Segment is KindValue
    )
    if len(Found) != 1:
        raise ValueError("Fusion link authoring needs one segment of each kind")
    return Found[0]


def TextItems(Value: KEntityValue) -> tuple[tuple[str, str], ...]:
    if not isinstance(Value, ValueMap):
        raise ValueError("Fusion link authoring expected a text map")
    Pairs = tuple((Entry.First, Entry.Second) for Entry in Value.Entries)
    if any(
        type(First) is not str or type(Second) is not str for First, Second in Pairs
    ):
        raise ValueError("Fusion link authoring expected a text map")
    return tuple((str(First), str(Second)) for First, Second in Pairs)
