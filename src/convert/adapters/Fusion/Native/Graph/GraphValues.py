from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def SeriesItems(Value: KEntityValue) -> tuple[KEntityValue, ...]:
    if not isinstance(Value, ValueSeries):
        raise ValueError("Native Fusion semantic field requires a sequence")
    return Value.Items


def MappingItems(Value: KEntityValue) -> tuple[ValuePair[KEntityValue], ...]:
    if not isinstance(Value, ValueMap):
        raise ValueError("Native Fusion semantic field requires a map")
    return Value.Entries


def NumberValue(Value: KEntityValue) -> float:
    if type(Value) not in (int, float) or not IsFinite(CastValue(float | int, Value)):
        raise ValueError("Native Fusion semantic field requires a finite number")
    return float(CastValue(float | int, Value))


def TextValue(Value: KEntityValue) -> str:
    if not isinstance(Value, str):
        raise ValueError("Native Fusion semantic field requires text")
    return Value


def ObjectFields(Value: KEntityValue) -> dict[str, KEntityValue]:
    if isinstance(Value, OptionalValue):
        Value = Value.Value
    if isinstance(Value, ValueObject):
        return {
            Field.FieldName: Field.Value
            for Group in Value.Groups
            for Field in Group.Fields
        }
    if isinstance(Value, ValueStruct):
        return {Field.FieldName: Field.Value for Field in Value.Fields}
    raise ValueError("Native Fusion semantic field requires a value object")


def PointCoords(Value: KEntityValue) -> tuple[float, float, float]:
    Fields = ObjectFields(Value)
    return NumberValue(Fields["x"]), NumberValue(Fields["y"]), NumberValue(Fields["z"])


def CheckIdentity(Value: KEntityValue) -> None:
    if not isinstance(Value, MatrixValue) or Value.Entries not in (
        None,
        (
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ),
    ):
        raise ValueError("Native Fusion profile requires identity placement")
