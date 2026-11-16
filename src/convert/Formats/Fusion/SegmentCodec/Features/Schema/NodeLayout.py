from convert.Formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.Formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

# node layout must remain consistent across callers so native records retain their segment ownership and schema
KNodeLayout = ClassLayout(
    ClassStamp(
        "A0A15D26-1F3B-4120-A3F1-9CDDA189AB74",
        "CB844AB6-240D-4fc9-9C9F-3679DC896D6F",
        2,
    ),
    (
        FieldSpec("isActive", FieldKind.KBoolean),
        FieldSpec("isEdited", FieldKind.KBoolean),
        FieldSpec("isEliminated", FieldKind.KBoolean),
        FieldSpec("rDynamicUpdateData", FieldKind.KStrongRef),
        FieldSpec("rGroupRepresentative", FieldKind.KPassiveRef),
        FieldSpec("rParentFeature", FieldKind.KPassiveRef),
    ),
)
