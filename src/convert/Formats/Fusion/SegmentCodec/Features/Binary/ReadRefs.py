from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureRefs
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.Formats.Fusion.SegmentCodec.Features.Binary.ReadLocalRef import (
    ReadLocalRefMut,
)


# the references operation needs a distinct decoding boundary so native records retain their segment ownership and schema
def ReadRefsMut(
    Cursor: MetaCursor, KindValue: FieldKind
) -> tuple[LocalRef | None, ...]:
    Values = tuple(
        ReadLocalRefMut(Cursor) for _ in range(Cursor.ReadCount(KMaxFeatureRefs))
    )
    if KindValue is FieldKind.KStrongSet and len(set(Values)) != len(Values):
        raise ValueError("Duplicate Fusion feature set reference")
    return Values
