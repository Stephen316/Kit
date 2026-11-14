from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Vocabulary.WireJson import WireJson


def ReadWireType(Value: WireJson) -> WireType:
    return WireType(
        Value["KindValue"],
        tuple(ReadWireType(Entry) for Entry in Value.get("Arguments", [])),
        tuple(
            FieldSpec(
                Entry["FieldName"], ReadWireType(Entry["ValueType"]), Entry["IsSaved"]
            )
            for Entry in Value.get("Members", [])
        ),
        Value.get("ClassGuid", ""),
        Value.get("FixedCount", 0),
        tuple(Value.get("AllowedInts", [])),
        Value.get("HasMatrixRows", False),
    )
