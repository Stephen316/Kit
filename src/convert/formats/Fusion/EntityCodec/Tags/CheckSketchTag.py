from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Tags.SketchFields import KSketchFields


def CheckSketchTag(Value: ValueStruct[KEntityValue]) -> None:
    Indexed = {Field.FieldName: Field.Value for Field in Value.Fields}
    if len(Indexed) != len(Value.Fields) or set(Indexed) != {
        Field.FieldName for Field in KSketchFields
    }:
        raise ValueError("Fusion sketch tag fields do not match the qualified schema")
    Sequence = Indexed["splitSequenceId"]
    TotalCount = Indexed["splitTotalNumber"]
    if (
        type(Sequence) is not int
        or type(TotalCount) is not int
        or not 1 <= Sequence <= TotalCount <= 0xFFFFFFFF
    ):
        raise ValueError("Fusion sketch tag requires a one-based split ordinal")
