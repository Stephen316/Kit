from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureRefs
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadLocalRef import (
    ReadLocalRefMut,
)


def ReadRefsMut(
    Cursor: MetaCursor, KindValue: FieldKind
) -> tuple[LocalRef | None, ...]:
    Values = tuple(
        ReadLocalRefMut(Cursor) for _ in range(Cursor.ReadCount(KMaxFeatureRefs))
    )
    if KindValue is FieldKind.KStrongSet and len(set(Values)) != len(Values):
        raise ValueError("Duplicate Fusion feature set reference")
    return Values
