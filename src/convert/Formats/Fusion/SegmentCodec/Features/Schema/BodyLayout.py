from convert.Formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.Formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

# body layout must remain consistent across callers so native records retain their segment ownership and schema
KBodyLayout = ClassLayout(
    ClassStamp(
        "666BFBBC-2150-4C5F-AAF7-09AB3C3D9E47",
        "A2052F46-21B4-4AAA-9AF1-C371F0AB6CAB",
        0,
    ),
    (FieldSpec("targetDataRefs", FieldKind.KStrongVector),),
)
