from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaOffset
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaProperty
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment

KSegmentTypes: tuple[type[object], ...] = (
    LocalRef,
    MetaHeader,
    MetaClass,
    MetaOffset,
    MetaProperty,
    MetaSegment,
)
