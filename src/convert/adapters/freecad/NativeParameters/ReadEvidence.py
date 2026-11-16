from collections.abc import Mapping
from re import compile as CompileRegex

from convert.adapters.freecad.Archive import IsPayloadMap
from convert.adapters.freecad.NativeParameters.ReadSheet import (
    KLiteral,
    ReadLiteral,
    ReadNodes,
)
from convert.adapters.freecad.Protocol import KRuleValueKindByCode, KScalarPropKinds
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue

# integer evidence must obey the native integer parser rather than float normalization
KRawInteger = CompileRegex(r"[+-]?[0-9]{1,64}")

# constraint evidence is recorded only for bounded indexed dimensional property owners
KRulePath = CompileRegex(r"Constraints\[[0-9]{1,6}\]")


# persisted numeric text must remain finite before native default values acquire dependency authority
def ReadRawValue(
    Source: object, KindValue: ValueKind, UnitName: str
) -> ParameterValue | None:
    if not isinstance(Source, str) or len(Source) > 128:
        return None
    Literal = Source.strip()
    Match = KLiteral.fullmatch(Literal)
    if Match is None or Match["unit"]:
        return None
    if KindValue == ValueKind.KInteger:
        return (
            ParameterValue(int(Literal), KindValue, UnitName)
            if KRawInteger.fullmatch(Literal)
            else None
        )
    if KindValue not in {ValueKind.KNumber, ValueKind.KLength, ValueKind.KAngle}:
        return None
    Value = ReadLiteral(f"{Literal} {UnitName}")
    return (
        Value
        if Value is not None and Value.kind == KindValue and Value.unit == UnitName
        else None
    )


# actual property type and scalar child must corroborate the parser recorded value
def ReadPropValue(
    Fields: Mapping[str, object], FieldPath: str
) -> ParameterValue | None:
    Attributes = Fields.get("attributes")
    if Fields.get("tag") != "Property" or not IsPayloadMap(Attributes):
        return None
    TypeName = Attributes.get("type")
    Shape = KScalarPropKinds.get(TypeName) if isinstance(TypeName, str) else None
    if Shape is None or Attributes.get("name") != FieldPath:
        return None
    KindValue, UnitName, TagName = Shape
    Children = ReadNodes(Fields.get("children", ()), 16)
    if len(Children) != 1 or Children[0].get("tag") != TagName:
        return None
    Scalar = Children[0].get("attributes")
    if not IsPayloadMap(Scalar) or Children[0].get("children"):
        return None
    return ReadRawValue(Scalar.get("value"), KindValue, UnitName)


# dimensional constraints retain their raw type and value independently from permissive native defaults
def ReadRuleValue(
    Fields: Mapping[str, object], FieldPath: str
) -> ParameterValue | None:
    RuleCode = Fields.get("Type")
    if not KRulePath.fullmatch(FieldPath) or not isinstance(RuleCode, str):
        return None
    if not 1 <= len(RuleCode) <= 3 or not RuleCode.isascii() or not RuleCode.isdigit():
        return None
    Shape = KRuleValueKindByCode.get(int(RuleCode))
    return ReadRawValue(Fields.get("Value"), *Shape) if Shape is not None else None


# synthetic expression placeholders and malformed saved scalars cannot establish evaluated equivalence
def HasSavedValue(Param: Parameter) -> bool:
    FieldPath = Param.attributes.get("freecad_path")
    if (
        not isinstance(FieldPath, str)
        or len(FieldPath) > 1024
        or isinstance(Param.value.value, bool)
    ):
        return False
    Property = Param.attributes.get("freecad_property")
    Constraint = Param.attributes.get("freecad_constraint")
    try:
        if IsPayloadMap(Property) and Constraint is None:
            Value = ReadPropValue(Property, FieldPath)
        elif IsPayloadMap(Constraint) and Property is None:
            Value = ReadRuleValue(Constraint, FieldPath)
        else:
            return False
    except (ValueError, OverflowError):
        return False
    return Value is not None and Value == Param.value
