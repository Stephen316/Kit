# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections import Counter as CountValues
from dataclasses import dataclass as MakeDataClass
from re import fullmatch as FullMatch
from typing import Mapping
from typing import cast as CastValue

from convert.adapters.freecad.LiteralQuantity import IsLiteralQty
from convert.geometry.Formula.Arithmetic import (
    EvalFormula,
    IsMatchingQty,
    ReadFormula,
    WriteFormula,
)
from interchange.records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.serialization.Deserialize import FromData


# only a fully bound and evaluated source expression may become a spreadsheet cell
@MakeDataClass(frozen=True, slots=True)
class FormulaPlan:
    Content: str
    References: tuple[str, ...]


# exact source wire records retain the parameter definitions needed for dimensional proof
def ReadFusionRows(Parameters: list[dict[str, object]]) -> dict[str, Parameter]:
    Counts = CountValues(
        Identity for Value in Parameters if isinstance(Identity := Value.get("id"), str)
    )
    Result: dict[str, Parameter] = {}
    for Value in Parameters:
        Identity = Value.get("id")
        if not isinstance(Identity, str) or Counts[Identity] != 1:
            continue
        ExpressionData = Value.get("expression")
        if (
            not isinstance(ExpressionData, dict)
            or CastValue(dict[str, object], ExpressionData).get("language") != "fusion"
        ):
            continue
        try:
            TypedValue = FromData(
                {
                    KeyName: Value[KeyName]
                    for KeyName in ("$type", "id", "name", "value", "expression")
                }
            )
        except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
            continue
        if (
            isinstance(TypedValue, Parameter)
            and isinstance(TypedValue.expression, Expression)
            and isinstance(CastValue(object, TypedValue.value), ParameterValue)
        ):
            Result[Identity] = TypedValue
    return Result


# aliases in this subset cannot be interpreted as cell addresses or unit names
def IsFormulaAlias(Alias: str) -> bool:
    return FullMatch(r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+", Alias) is not None


# source tokens must resolve solely through the explicitly stored parameter ids
def ReadFormulaRefs(
    Names: tuple[str, ...],
    References: tuple[str, ...],
    Parameters: Mapping[str, Parameter],
    Aliases: Mapping[str, str],
) -> tuple[dict[str, ParameterValue], dict[str, str]] | None:
    if len(set(References)) != len(References):
        return None
    Values: dict[str, ParameterValue] = {}
    AliasNames: dict[str, str] = {}
    for Identity in References:
        ParameterRow = Parameters.get(Identity)
        Alias = Aliases.get(Identity)
        if (
            ParameterRow is None
            or ParameterRow.name in Values
            or Alias is None
            or not IsFormulaAlias(Alias)
        ):
            return None
        NameValue = ParameterRow.name
        Values[NameValue] = ParameterRow.value
        AliasNames[NameValue] = Alias
    if set(Names) != Values.keys():
        return None
    return Values, AliasNames


# validating both stored dimensions and value prevents a stale formula from becoming live
def ReadFusionPlan(
    ParameterData: Parameter,
    Parameters: Mapping[str, Parameter],
    Aliases: Mapping[str, str],
) -> FormulaPlan | None:
    ExpressionValue = ParameterData.expression
    if ExpressionValue is None:
        return None
    SourceText = ExpressionValue.source.strip()
    if not SourceText or any(Value in SourceText for Value in ("\n", "\r", ";")):
        return None
    References = ExpressionValue.parameter_ids
    ValueData = ParameterData.value
    if not References and IsLiteralQty(
        SourceText, ValueData.kind, ValueData.value, ValueData.unit
    ):
        return FormulaPlan(SourceText, References)
    FormulaValue = ReadFormula(SourceText)
    if FormulaValue is None:
        return None
    Resolved = ReadFormulaRefs(FormulaValue.Names, References, Parameters, Aliases)
    if Resolved is None:
        return None
    Values, AliasNames = Resolved
    Evaluated = EvalFormula(FormulaValue, Values)
    if Evaluated is None or not IsMatchingQty(Evaluated, ValueData):
        return None
    Content = WriteFormula(FormulaValue, AliasNames)
    return FormulaPlan(Content, References) if Content is not None else None
