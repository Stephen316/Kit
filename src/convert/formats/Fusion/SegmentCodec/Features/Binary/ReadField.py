from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText
from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Binary.CheckUuid import CheckUuid
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadLocalRef import (
    ReadLocalRefMut,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadRefs import ReadRefsMut
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadScalar import ReadScalarMut
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadVector import ReadVectorMut
from convert.formats.Fusion.SegmentCodec.Features.Binary.RefKinds import (
    KCollectionKinds,
    KReferenceKinds,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.ScalarKinds import KScalarKinds


def ReadFieldMut(Cursor: MetaCursor, KindValue: FieldKind) -> KFieldValue:
    if KindValue in KScalarKinds:
        return ReadScalarMut(Cursor, KindValue)
    if KindValue in (FieldKind.KUnicode, FieldKind.KUuidText):
        Value = Cursor.ReadText(True, Maximum=KMaxFeatureText, AllowControls=True)
        if KindValue is FieldKind.KUuidText:
            CheckUuid(Value)
        return Value
    if KindValue is FieldKind.KVector:
        return ReadVectorMut(Cursor)
    if KindValue in KReferenceKinds:
        return ReadLocalRefMut(Cursor)
    if KindValue in KCollectionKinds:
        return ReadRefsMut(Cursor, KindValue)
    raise ValueError("Unsupported Fusion feature field type")
