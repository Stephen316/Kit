from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Vocabulary.ReadWireType import ReadWireType
from convert.formats.Fusion.EntityCodec.Vocabulary.SchemaJson import SchemaJson


def ReadSchema(Value: SchemaJson) -> ClassSchema:
    return ClassSchema(
        Value["ClassGuid"],
        Value["BaseGuid"],
        Value["SchemaVersion"],
        tuple(
            FieldSpec(
                Entry["FieldName"], ReadWireType(Entry["ValueType"]), Entry["IsSaved"]
            )
            for Entry in Value["Members"]
        ),
        Value["IsValue"],
    )
