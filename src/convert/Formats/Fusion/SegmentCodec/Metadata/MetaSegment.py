from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.SegmentCodec.Metadata.MetaContext import MetaContext
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import (
    MetaClass,
    MetaOffset,
    MetaProperty,
)


# an immutable segment retains the fields discarded by the projection index
@MakeDataClass(frozen=True, slots=True)
class MetaSegment:
    Header: MetaHeader
    Classes: tuple[MetaClass, ...]
    StoredIds: tuple[int, ...]
    Primary: tuple[MetaOffset, ...]
    Continuations: tuple[MetaOffset, ...]
    NextId: int
    Reserved: int
    Properties: tuple[MetaProperty, ...]
    Contexts: tuple[MetaContext, ...] = ()
