from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KToolLayout = ClassLayout(
    ClassStamp(
        "60F291CB-499B-4AB1-B0E5-340368671724",
        "E8BDB9D4-2E39-405C-B05E-E2206AD3F125",
        0,
    ),
    (FieldSpec("toolbodyCaches", FieldKind.KStrongVector),),
)
