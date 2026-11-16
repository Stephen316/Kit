from convert.Formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.Formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

# compute layout must remain consistent across callers so native records retain their segment ownership and schema
KComputeLayout = ClassLayout(
    ClassStamp(
        "E8BDB9D4-2E39-405C-B05E-E2206AD3F125",
        "6370B480-4C9F-4AF3-A8DD-D364B7AF7275",
        3,
    ),
    (
        FieldSpec("birthday", FieldKind.KUnsigned),
        FieldSpec("computeTime", FieldKind.KDecimal),
        FieldSpec("firstBirthday", FieldKind.KUnsigned),
        FieldSpec("status", FieldKind.KStrongRef),
    ),
)
