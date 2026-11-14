from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KProfileLayout = ClassLayout(
    ClassStamp(
        "3FED63D9-CDC5-4334-A5C5-6C10271320D5",
        "2EDC2536-D95B-4469-8ACA-DC07124D9C43",
        1,
    ),
    (FieldSpec("profileDataRefs", FieldKind.KStrongVector),),
)
