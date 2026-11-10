# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue
from decimal import Decimal
from math import isfinite as IsFinite
from re import compile as CompilePattern

# a text bound keeps lexing independent of the surrounding archive size
KMaxTextSize = 65536

# token counts bound memory separately from long property names
KMaxTokenCount = 4096

# decimal literals can include the scientific notation used on native save
KNumberText = r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"

# indexed sketch paths retain their exact native geometry slots
KNameText = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*(?:\[[0-9]+\])?)*"

# native path references and numbers need distinct lexical identities
KTokenPattern = CompilePattern(
    rf"[ \t\r\n]*(?:(?P<Number>{KNumberText})|(?P<Names>{KNameText})|(?P<Literal><<Reversed>>)|(?P<Punct><=|>=|==|[()+*/%<>;?\-:]))"
)

# operand tokens keep literal text until the parser consumes its unit
KExprToken = tuple[str, str]


# expression text must fit the native grammar before structural comparison
def ReadExprTokens(TextValue: str) -> tuple[KExprToken, ...]:
    if (
        not isinstance(CastValue(object, TextValue), str)
        or len(TextValue) > KMaxTextSize
    ):
        raise ValueError("invalid plane expression size")
    TextValue = TextValue.rstrip(" \t\r\n")
    Tokens: list[KExprToken] = []
    Index = 0
    while Index < len(TextValue):
        Match = KTokenPattern.match(TextValue, Index)
        if Match is None or Match.lastgroup is None or len(Tokens) >= KMaxTokenCount:
            raise ValueError("invalid plane expression token")
        Tokens.append((Match.lastgroup, Match.group(Match.lastgroup)))
        Index = Match.end()
    return tuple(Tokens)


# genuine literals come from finite native double precision properties
def ReadExprNumber(NumberText: str) -> Decimal:
    if len(NumberText) > 64:
        raise ValueError("invalid plane expression number size")
    Number = Decimal(NumberText)
    FloatValue = float(Number)
    if not IsFinite(FloatValue) or (FloatValue == 0.0 and not Number.is_zero()):
        raise ValueError("invalid plane expression number range")
    return Number
