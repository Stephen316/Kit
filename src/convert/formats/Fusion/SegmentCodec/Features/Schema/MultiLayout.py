from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KMultiLayout = ClassLayout(
    ClassStamp(
        "2EDC2536-D95B-4469-8ACA-DC07124D9C43",
        "666BFBBC-2150-4C5F-AAF7-09AB3C3D9E47",
        2,
    ),
    (
        FieldSpec("cachedDcBodies", FieldKind.KStrongSet),
        FieldSpec("dcBodies", FieldKind.KStrongVector),
        FieldSpec("removedBodies", FieldKind.KPassiveVector),
    ),
)
