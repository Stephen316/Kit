from convert.Formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec


# the persist fields contract needs a shared interpretation so native records retain their segment ownership and schema
def PersistFields(Layout: ClassLayout) -> tuple[FieldSpec, ...]:

    # ordering by field name text must stay deterministic so segment reconstruction resolves equivalent inputs consistently
    return tuple(
        sorted(
            (Field for Field in Layout.Members if Field.FlagMask & 1),
            key=lambda Field: Field.NameText,
        )
    )
