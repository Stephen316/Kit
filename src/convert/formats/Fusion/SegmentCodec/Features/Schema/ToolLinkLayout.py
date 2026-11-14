from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KToolLinkLayout = ClassLayout(
    ClassStamp(
        "0897AF07-EF1B-42E5-BDD9-1C746A085CBC",
        "60F291CB-499B-4AB1-B0E5-340368671724",
        0,
    ),
    (FieldSpec("rExtrudeFeature", FieldKind.KPassiveRef),),
)
