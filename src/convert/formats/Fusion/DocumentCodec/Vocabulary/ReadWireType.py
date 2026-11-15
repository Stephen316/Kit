from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    IsTrueValue,
    ReadInteger,
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import KWireKind, WireType


# the wire type operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadWireType(Value: object) -> WireType:
    Fields = ReadObject(Value)
    return WireType(
        CastValue(KWireKind, ReadString(Fields["KindValue"])),
        tuple(ReadWireType(Entry) for Entry in ReadSeries(Fields.get("Arguments", []))),
        tuple(ReadFieldSpec(Entry) for Entry in ReadSeries(Fields.get("Members", []))),
        ReadString(Fields.get("ClassGuid", "")),
        ReadInteger(Fields.get("FixedCount", 0)),
        tuple(
            ReadInteger(Entry) for Entry in ReadSeries(Fields.get("AllowedInts", []))
        ),
        IsTrueValue(Fields.get("HasMatrixRows", False)),
    )


# the field specification operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadFieldSpec(Value: object) -> FieldSpec[WireType]:
    Fields = ReadObject(Value)
    return FieldSpec(
        ReadString(Fields["FieldName"]),
        ReadWireType(Fields["ValueType"]),
        IsTrueValue(Fields.get("IsSaved", True)),
    )
