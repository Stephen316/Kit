from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Binary.CheckUuid import CheckUuid
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitLocalRef import (
    EmitLocalRef,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitRefs import EmitRefs
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitScalar import EmitScalar
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitVector import EmitVector
from convert.formats.Fusion.SegmentCodec.Features.Binary.RefKinds import (
    KCollectionKinds,
    KReferenceKinds,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.ScalarKinds import KScalarKinds


def EmitField(KindValue: FieldKind, Value: KFieldValue) -> bytes:
    if KindValue in KScalarKinds:
        return EmitScalar(KindValue, Value)
    if KindValue in (FieldKind.KUnicode, FieldKind.KUuidText):
        if type(Value) is not str:
            raise ValueError("Fusion feature string requires text")
        if KindValue is FieldKind.KUuidText:
            CheckUuid(Value)
        return EmitText(Value, True)
    if KindValue is FieldKind.KVector:
        return EmitVector(Value)
    if KindValue in KReferenceKinds:
        return EmitLocalRef(Value)
    if KindValue in KCollectionKinds:
        return EmitRefs(KindValue, Value)
    raise ValueError("Unsupported Fusion feature field type")
