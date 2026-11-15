from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from tests.convert.formats.FusionCodec.Entities.WireJson import WireJson


# shared read wire setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadWire(Value: WireJson) -> WireType:
    return WireType(
        Value["KindValue"],
        tuple(ReadWire(Entry) for Entry in Value.get("Arguments", [])),
        tuple(
            FieldSpec(
                Entry["FieldName"], ReadWire(Entry["ValueType"]), Entry["IsSaved"]
            )
            for Entry in Value.get("Members", [])
        ),
        Value.get("ClassGuid", ""),
        Value.get("FixedCount", 0),
        tuple(Value.get("AllowedInts", [])),
        Value.get("HasMatrixRows", False),
    )
