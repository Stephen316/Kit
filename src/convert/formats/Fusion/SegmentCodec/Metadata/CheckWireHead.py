from typing import cast as CastValue
from convert.formats.Fusion.MetaIndex import KSegmentLayout, SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader


# both directions qualify the same version and segment layout before handling records
def CheckWireHead(Header: MetaHeader) -> None:
    if not isinstance(CastValue(object, Header), MetaHeader) or not isinstance(
        CastValue(object, Header.Segment), SegmentKind
    ):
        raise ValueError("Unsupported Fusion MetaStream segment kind")
    ExpectedId, ExpectedStorage = KSegmentLayout[Header.Segment]
    if (
        Header.Magic != 1234
        or Header.Version != 8
        or Header.RepeatedKind != Header.Segment.value
        or type(Header.HeaderWords) is not tuple
        or len(CastValue(tuple[object, ...], Header.HeaderWords)) != 2
        or type(Header.StorageWords) is not tuple
        or Header.StorageWords != ExpectedStorage
        or (ExpectedId is not None and Header.SegmentId != ExpectedId)
    ):
        raise ValueError("Unsupported Fusion MetaStream header")
