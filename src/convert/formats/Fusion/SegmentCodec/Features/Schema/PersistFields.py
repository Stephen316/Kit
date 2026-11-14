from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec


def PersistFields(Layout: ClassLayout) -> tuple[FieldSpec, ...]:
    return tuple(
        sorted(
            (Field for Field in Layout.Members if Field.FlagMask & 1),
            key=lambda Field: Field.NameText,
        )
    )
