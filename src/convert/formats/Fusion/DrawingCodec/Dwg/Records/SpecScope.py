import re as Regex

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsFloat,
    AsInt,
    AsRecords,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecOp import SpecOp

KScopes = tuple[list[DwgField], ...]
KConditionPattern = Regex.compile(
    r"^([A-Za-z][A-Za-z0-9.]*)(==|!=|!&|&|<|>=)(-?(?:0x[0-9A-Fa-f]+|[0-9]+))$"
)
KBranchKinds = frozenset({"if", "since", "until"})


def LookupValue(FieldName: str, Scopes: KScopes) -> KDwgValue:
    for Fields in Scopes:
        for Entry in reversed(Fields):
            if Entry.FieldName == FieldName:
                return Entry.FieldValue
    raise ValueError(f"DWG record field {FieldName!r} is used before it is read")


def LookupCount(CountText: str, Scopes: KScopes) -> int:
    if Regex.fullmatch(r"[0-9]+", CountText):
        return int(CountText)
    Value = LookupValue(CountText, Scopes)
    if isinstance(Value, (bytes, tuple)):
        return len(Value)
    return AsInt(Value)


def LookupFloat(DefaultText: str, Scopes: KScopes) -> float:
    if Regex.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", DefaultText):
        return float(DefaultText)
    return AsFloat(LookupValue(DefaultText, Scopes))


def FlagValues(LeftText: str, Scopes: KScopes) -> tuple[int, ...]:
    ListName, _, FieldName = LeftText.partition(".")
    if not FieldName:
        return (AsInt(LookupValue(ListName, Scopes)),)
    Items = AsRecords(LookupValue(ListName, Scopes))
    return tuple(
        AsInt(Entry.FieldValue)
        for ItemRecord in Items
        for Entry in ItemRecord.RecordFields
        if Entry.FieldName == FieldName
    )


def IsSpecTrue(Condition: str, Scopes: KScopes) -> bool:
    Matched = KConditionPattern.match(Condition)
    if Matched is None:
        raise ValueError(f"DWG record condition {Condition!r} is malformed")
    Right = int(Matched[3], 0)
    Operator = Matched[2]
    return any(
        IsCompareTrue(LeftValue, Operator, Right)
        for LeftValue in FlagValues(Matched[1], Scopes)
    )


def IsCompareTrue(LeftValue: int, Operator: str, Right: int) -> bool:
    if Operator == "==":
        return LeftValue == Right
    if Operator == "!=":
        return LeftValue != Right
    if Operator == "&":
        return LeftValue & Right != 0
    if Operator == "!&":
        return LeftValue & Right == 0
    return LeftValue < Right if Operator == "<" else LeftValue >= Right


def IsBranchTrue(Operation: SpecOp, Scopes: KScopes, VersionText: str) -> bool:
    if Operation.OpKind == "since":
        return VersionText >= Operation.OpName
    if Operation.OpKind == "until":
        return VersionText < Operation.OpName
    return IsSpecTrue(Operation.OpName, Scopes)
