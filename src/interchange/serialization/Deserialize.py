# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import base64 as BaseCodec
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase

from interchange.serialization.DecodeRecord import DecodeRecord
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.TypeRegistry import KTypeRegistry
from interchange.serialization.WireData import CheckWireData
from typing import cast as CastValue


# recursive decoding validates registered types before constructing immutable model records
def FromData(SourceValue: object) -> object:
    DataValue = CheckWireData(SourceValue)
    if isinstance(DataValue, list):
        return [FromData(ItemValue) for ItemValue in DataValue]
    if not isinstance(DataValue, dict):
        return DataValue
    KeyValues = set(DataValue)
    if KeyValues == {"$bytes"}:
        EncodedValue = DataValue["$bytes"]
        if not isinstance(EncodedValue, str):
            raise ValueError("encoded bytes must be text")
        return BaseCodec.b64decode(EncodedValue, validate=True)
    if KeyValues in ({"$tuple"}, {"$frozenset"}, {"$set"}):
        TagName = next(iter(KeyValues))
        ItemValues = DataValue[TagName]
        if not isinstance(ItemValues, list):
            raise ValueError(f"{TagName} value must be a list")
        DecodedValues = [FromData(ItemValue) for ItemValue in ItemValues]
        if TagName == "$tuple":
            return tuple(DecodedValues)
        if TagName == "$frozenset":
            return frozenset(DecodedValues)
        return set(DecodedValues)
    if "$enum" in DataValue:
        if KeyValues != {"$enum", "value"}:
            raise ValueError("encoded enum must contain only type and value")
        EnumName = DataValue["$enum"]
        if not isinstance(EnumName, str) or not EnumName:
            raise ValueError("encoded enum type must be nonempty text")
        EnumType = KTypeRegistry.get(EnumName)
        if EnumType is None or not issubclass(EnumType, EnumBase):
            raise ValueError(f"unknown enum type {EnumName!r}")
        return EnumType(FromData(DataValue["value"]))
    if "$type" not in DataValue:
        return {
            KeyValue: FromData(ItemValue) for KeyValue, ItemValue in DataValue.items()
        }
    WireType = DataValue["$type"]
    if not isinstance(WireType, str) or not WireType:
        raise ValueError("encoded record type must be nonempty text")
    TargetType = KTypeRegistry.get(WireType)
    if TargetType is None or not IsDataClass(TargetType):
        raise ValueError(f"unknown data type {WireType!r}")
    RecordType = CastValue(type[DataRecord], TargetType)
    return DecodeRecord(DataValue, RecordType, FromData)
