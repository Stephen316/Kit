from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText
from convert.Formats.Fusion.SegmentCodec.Features.Model.FeatureFrame import FeatureFrame
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.Formats.Fusion.SegmentCodec.Features.Binary.ReadScalar import ReadScalarMut
from convert.Formats.Fusion.SegmentCodec.Features.Binary.ReadSubjects import (
    ReadSubjectsMut,
)


# the frame operation needs a distinct decoding boundary so native records retain their segment ownership and schema
def ReadFrameMut(Cursor: MetaCursor, IsPrimary: bool) -> FeatureFrame:
    RootId = Cursor.ReadText(Maximum=KMaxFeatureText)
    if not IsPrimary:
        return FeatureFrame(RootId, None, False)
    HasSubjects = bool(ReadScalarMut(Cursor, FieldKind.KBoolean))
    Subjects = ReadSubjectsMut(Cursor) if HasSubjects else None
    HasNamedMeta = bool(ReadScalarMut(Cursor, FieldKind.KBoolean))
    if HasNamedMeta and Cursor.ReadWord() != 0:
        raise ValueError("Nonempty Fusion feature named metadata is unsupported")
    return FeatureFrame(RootId, Subjects, HasNamedMeta)
