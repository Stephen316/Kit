from __future__ import annotations

from dataclasses import fields as GetFields
from functools import lru_cache as Memoize

from interchange.core.Reflection import CanonName
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.WireFields import KTypeWireFields, KWireFields
from interchange.serialization.WireTypes import KWireTypes


# canonical slots across inheritance preserve storage access after historical reflection mutation
def GetSlotNames(ClassType: type[object]) -> tuple[str, ...]:
    SlotNames: list[str] = []
    for BaseType in reversed(ClassType.__mro__):
        BaseSlots = BaseType.__dict__.get("__slots__", ())
        SlotNames.extend(
            SlotName
            for SlotName in BaseSlots
            if isinstance(SlotName, str) and not SlotName.startswith("__")
        )
    return tuple(SlotNames)


# type registration needs stable names independent of internal model naming
def GetWireType(ClassType: type[object]) -> str:
    CanonicalName = CanonName(ClassType)
    return KWireTypes.get(CanonicalName, ClassType.__name__)


# field serialization needs predictable snake case without exposing it in source identifiers
def FormatWireName(FieldName: str) -> str:
    NameParts: list[str] = []
    for IndexValue, Character in enumerate(FieldName):
        PriorChar = FieldName[IndexValue - 1] if IndexValue else ""
        NextChar = FieldName[IndexValue + 1] if IndexValue + 1 < len(FieldName) else ""
        if (
            IndexValue
            and Character.isupper()
            and (PriorChar.islower() or PriorChar.isupper() and NextChar.islower())
        ):
            NameParts.append("_")
        NameParts.append(Character.casefold())
    return "".join(NameParts)


# boolean model fields omit their source marker on the historical wire format
def GetWireField(FieldName: str, ClassType: type[object] | None = None) -> str:
    if ClassType is not None:
        TypeFields = KTypeWireFields.get(CanonName(ClassType), {})
        if FieldName in TypeFields:
            return TypeFields[FieldName]
    if FieldName in KWireFields:
        return KWireFields[FieldName]
    SourceName = FieldName[2:] if FieldName.startswith("Is") else FieldName
    return FormatWireName(SourceName)


# deserialization needs the compliant field name corresponding to each historical wire key
def GetModelField(WireName: str, ClassType: type[object] | None = None) -> str:
    if WireName and WireName[0].isupper() and "_" not in WireName:
        return WireName
    if ClassType is not None:
        TypeFields = KTypeWireFields.get(CanonName(ClassType), {})
        for ModelField, WireField in TypeFields.items():
            if WireField == WireName:
                return ModelField
    ExplicitNames = {
        WireField: ModelField for ModelField, WireField in KWireFields.items()
    }
    return ExplicitNames.get(
        WireName,
        "".join(NamePart.title() for NamePart in WireName.split("_")),
    )


# known schema names can be indexed once without retaining untrusted incoming keys
@Memoize(maxsize=256)
def GetSlotAliases(
    SlotNames: tuple[str, ...], ModelName: str
) -> tuple[dict[str, str], frozenset[str]]:
    Positions: dict[str, int] = {}
    Aliases: dict[str, str] = {}
    TypeFields = KTypeWireFields.get(ModelName, {})
    for FieldName in SlotNames:
        _ = Positions.setdefault(FieldName, len(Positions))
        WireName = TypeFields.get(FieldName, GetWireField(FieldName))
        _ = Aliases.setdefault(WireName, FieldName)
    for WireName, FieldName in Aliases.items():
        Converted = TypeFields.get(WireName, GetWireField(WireName))
        if Converted in Positions and Positions[Converted] < Positions[FieldName]:
            Aliases[WireName] = Converted
    return Aliases, frozenset(Positions)


# target records disambiguate shared wire keys by their actual dataclass fields
def ResolveField(ClassType: type[DataRecord], WireName: str) -> str:
    SlotNames = GetSlotNames(ClassType)
    ModelName = CanonName(ClassType)
    if type(WireName) is str:
        Aliases, SlotSet = GetSlotAliases(SlotNames, ModelName)
        Direct = Aliases.get(WireName)
        if Direct is not None:
            return Direct
        Converted = GetWireField(WireName, ClassType)
        if Converted in SlotSet:
            return Converted
    else:
        TypeFields = KTypeWireFields.get(ModelName, {})
        for FieldName in SlotNames:
            if TypeFields.get(FieldName, GetWireField(FieldName)) == WireName:
                return FieldName
            if GetWireField(WireName, ClassType) == FieldName:
                return FieldName
    if WireName in {FieldValue.name for FieldValue in GetFields(ClassType)}:
        return WireName
    return GetModelField(WireName, ClassType)
