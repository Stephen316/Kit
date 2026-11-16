from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.Formats.Fusion.EntityCodec.Vocabulary.ReadWireType import ReadWireType
from convert.Formats.Fusion.EntityCodec.Vocabulary.SchemaJson import SchemaJson


# the schema operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
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
