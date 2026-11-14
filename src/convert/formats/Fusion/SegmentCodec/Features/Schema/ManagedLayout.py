from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KManagedLayout = ClassLayout(
    ClassStamp(
        "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
        "98542EB9-A4F2-4137-A808-DBB5B3CD6159",
        1,
    ),
    (
        FieldSpec("expanded", FieldKind.KBoolean, 0x30),
        FieldSpec("rParent", FieldKind.KPassiveRef),
    ),
)
