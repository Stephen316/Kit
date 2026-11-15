from json import loads as LoadJson
from pathlib import Path
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    IsTrueValue,
    ReadInteger,
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadWireType import ReadFieldSpec
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema


# the vocabulary operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadVocabulary(Source: Path) -> tuple[NativeSchema, ...]:
    Values = ReadSeries(CastValue(object, LoadJson(Source.read_text(encoding="utf-8"))))
    Result: list[NativeSchema] = []
    for Value in Values:
        Fields = ReadObject(Value)
        Schema = ClassSchema(
            ReadString(Fields["ClassGuid"]),
            ReadString(Fields["BaseGuid"]),
            ReadInteger(Fields["SchemaVersion"]),
            tuple(ReadFieldSpec(Entry) for Entry in ReadSeries(Fields["Members"])),
            IsTrueValue(Fields["IsValue"]),
        )
        Result.append(
            NativeSchema(
                ReadString(Fields["NameValue"]),
                ReadString(Fields["ClassSpace"]),
                Schema,
            )
        )
    return tuple(Result)
