from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# shared read fields setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadFields(Value: KEntityValue) -> dict[str, KEntityValue]:
    assert isinstance(Value, ValueStruct)
    return {Field.FieldName: Field.Value for Field in Value.Fields}


# shared read point setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadPoint(Value: KEntityValue) -> tuple[float, ...]:
    Fields = ReadFields(Value)
    Coordinates = tuple(Fields[AxisName] for AxisName in ("x", "y", "z"))
    assert all(isinstance(Coord, (int, float)) for Coord in Coordinates)
    return tuple(
        float(Coord) for Coord in Coordinates if isinstance(Coord, (int, float))
    )


# shared read scalar setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadScalar(Value: KEntityValue) -> float:
    assert isinstance(Value, (int, float))
    return float(Value)
