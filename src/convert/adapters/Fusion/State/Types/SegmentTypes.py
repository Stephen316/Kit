from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaOffset
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaProperty
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment

# the segment types order must stay explicit so public document claims remain grounded in native records
KSegmentTypes: tuple[type[object], ...] = (
    LocalRef,
    MetaHeader,
    MetaClass,
    MetaOffset,
    MetaProperty,
    MetaSegment,
)
