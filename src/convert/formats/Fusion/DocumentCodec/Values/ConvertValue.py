from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Values.ConvertFields import ConvertFields
from convert.formats.Fusion.DocumentCodec.Values.ConvertGroups import ConvertGroups
from convert.formats.Fusion.DocumentCodec.Values.ConvertRef import ConvertRef
from convert.formats.Fusion.DocumentCodec.Values.ConvertSeries import ConvertSeries
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Tags.SketchFields import KSketchFields


def ConvertMatrix(Value: object) -> MatrixValue:
    Fields = ReadObject(Value)
    if Fields == {"identity": True}:
        return MatrixValue(None)
    Entries = Fields.get("entries")
    if not isinstance(Entries, list):
        raise ValueError("Authored matrices require identity or sixteen entries")
    Values = list(CastValue(list[object], Entries))
    Numbers = [
        Entry for Entry in Values if isinstance(Entry, float) and IsFinite(Entry)
    ]
    if len(Numbers) != 16 or len(Values) != 16:
        raise ValueError("Authored matrices require sixteen finite float entries")
    return MatrixValue(tuple(Numbers))


def ConvertValue(
    Value: object, Shape: WireType, Catalog: dict[str, NativeSchema]
) -> KEntityValue:
    KindValue = Shape.KindValue
    if KindValue == "ref":
        return ConvertRef(Value)
    if KindValue == "optional":
        return (
            None
            if Value is None
            else OptionalValue(ConvertValue(Value, Shape.Arguments[0], Catalog))
        )
    if KindValue in ("sequence", "set", "fixed", "pair", "map"):
        return ConvertSeries(Value, Shape, Catalog, ConvertValue)
    if KindValue == "struct":
        return ValueStruct(ConvertFields(Value, Shape.Members, Catalog, ConvertValue))
    if KindValue == "sketch-tag":
        return ValueStruct(ConvertFields(Value, KSketchFields, Catalog, ConvertValue))
    if KindValue == "object":
        return ValueObject(ConvertGroups(Value, Catalog, ConvertValue))
    if KindValue == "matrix":
        return ConvertMatrix(Value)
    if KindValue == "recipe" and isinstance(Value, RecipeValue):
        return Value
    if KindValue != "unsupported" and isinstance(Value, (bool, int, float, str)):
        return Value
    raise ValueError("Unsupported authored semantic value")
