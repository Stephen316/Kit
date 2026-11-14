from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadObject,
    ReadSeries,
)
from convert.formats.Fusion.DocumentCodec.Values.ValueConverter import KValueConverter
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


def ConvertSeries(
    Value: object,
    Shape: WireType,
    Catalog: dict[str, NativeSchema],
    Converter: KValueConverter,
) -> ValueSeries[KEntityValue] | ValueMap[KEntityValue] | ValuePair[KEntityValue]:
    if Shape.KindValue in ("sequence", "set", "fixed"):
        return ValueSeries(
            tuple(
                Converter(Entry, Shape.Arguments[0], Catalog)
                for Entry in ReadSeries(Value)
            )
        )
    if Shape.KindValue == "pair":
        Fields = ReadObject(Value)
        if set(Fields) != {"first", "second"}:
            raise ValueError("Invalid authored pair fields")
        return ValuePair(
            Converter(Fields["first"], Shape.Arguments[0], Catalog),
            Converter(Fields["second"], Shape.Arguments[1], Catalog),
        )
    Entries: list[ValuePair[KEntityValue]] = []
    for Entry in ReadSeries(Value):
        Fields = ReadObject(Entry)
        if set(Fields) != {"key", "value"}:
            raise ValueError("Invalid authored map fields")
        Entries.append(
            ValuePair(
                Converter(Fields["key"], Shape.Arguments[0], Catalog),
                Converter(Fields["value"], Shape.Arguments[1], Catalog),
            )
        )
    return ValueMap(tuple(Entries))
