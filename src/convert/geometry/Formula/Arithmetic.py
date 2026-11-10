# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from ast import (
    Add,
    BinOp,
    Div,
    Load,
    Mult,
    Name,
    Sub,
    UAdd,
    USub,
    UnaryOp,
    expr as ExprNode,
    parse as ParseAst,
    walk as WalkAst,
)
from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass

from convert.geometry.Formula.FormulaEval import EvalNode
from convert.geometry.Formula.FormulaTokens import FormulaAtom, KNamePattern, ReadTokens
from convert.geometry.Formula.FormulaUnits import (
    KFormulaUnits,
    KQuantity,
    IsMatchingQty as IsMatchingQty,
)
from interchange.records.RecordParameter import ParameterValue

# built in constants and unit names cannot serve as unambiguous parameter names
KReservedNames = frozenset((*KFormulaUnits, "pi", "e", "true", "false"))


# one expression representation keeps name resolution and output on the same grammar
@MakeDataClass(frozen=True, slots=True)
class Formula:
    Names: tuple[str, ...]
    Tokens: tuple[str | FormulaAtom, ...]
    Atoms: tuple[FormulaAtom, ...]
    RootValue: ExprNode


# parsing placeholders avoids host language number name and unit syntax differences
def ReadFormula(Source: str) -> Formula | None:
    TokenValues = ReadTokens(Source)
    if not TokenValues:
        return None
    Atoms: list[FormulaAtom] = []
    Syntax: list[str] = []
    for TokenValue in TokenValues:
        if isinstance(TokenValue, FormulaAtom):
            Syntax.append(f"operand{len(Atoms)}")
            Atoms.append(TokenValue)
        else:
            Syntax.append(TokenValue)
    try:
        TreeValue = ParseAst(" ".join(Syntax), mode="eval").body
    except (SyntaxError, ValueError, RecursionError):
        return None
    if any(
        not isinstance(
            Value, (BinOp, UnaryOp, Name, Load, Add, Sub, Mult, Div, UAdd, USub)
        )
        for Value in WalkAst(TreeValue)
    ):
        return None
    Names = tuple(
        dict.fromkeys(Value.TextValue for Value in Atoms if Value.Quantity is None)
    )
    if any(Value.casefold() in KReservedNames for Value in Names):
        return None
    return Formula(Names, TokenValues, tuple(Atoms), TreeValue)


# callers need a checked value before admitting source dependencies or native output
def EvalFormula(
    FormulaValue: Formula, Values: Mapping[str, ParameterValue]
) -> KQuantity | None:
    try:
        return EvalNode(FormulaValue.RootValue, FormulaValue.Atoms, Values)
    except (ArithmeticError, KeyError, ValueError, RecursionError):
        return None


# writable drivers must be literal quantities rather than hidden constant formulas
def IsLiteralExpr(FormulaValue: Formula) -> bool:
    RootValue = FormulaValue.RootValue
    if isinstance(RootValue, UnaryOp):
        RootValue = RootValue.operand
    return not FormulaValue.Names and isinstance(RootValue, Name)


# aliases replace only resolved operand names and never units or substrings
def WriteFormula(FormulaValue: Formula, Aliases: Mapping[str, str]) -> str | None:
    Names = tuple(Aliases.get(Value, "") for Value in FormulaValue.Names)
    if len(set(Names)) != len(Names) or any(
        not KNamePattern.fullmatch(Value) for Value in Names
    ):
        return None
    return " ".join(
        (
            TokenValue
            if isinstance(TokenValue, str)
            else (
                TokenValue.TextValue
                if TokenValue.Quantity is not None
                else Aliases[TokenValue.TextValue]
            )
        )
        for TokenValue in FormulaValue.Tokens
    )
