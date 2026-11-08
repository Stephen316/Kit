# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite
from re import compile as CompileRegex

from convert.geometry.Formula.FormulaUnits import KFormulaUnits, KQuantity

# identifier boundaries keep a name separate from similarly prefixed parameters
KNamePattern = CompileRegex(r"[A-Za-z_][A-Za-z_0-9]*")

# source arithmetic can contain only decimal quantities names and closed operators
KTokenPattern = CompileRegex(
    r"(?P<number>(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)"
    r"|(?P<name>[A-Za-z_][A-Za-z_0-9]*)|(?P<operator>[()+*/-])|(?P<space>[ \t]+)"
)


# atoms preserve source spelling separately from their canonical physical value
@MakeDataClass(frozen=True, slots=True)
class FormulaAtom:
    TextValue: str
    Quantity: KQuantity | None = None


# the lexer validates every character before parsing or emitting native expressions
def ReadTokens(Source: str) -> tuple[str | FormulaAtom, ...] | None:
    if not isinstance(Source, str) or not Source or len(Source) > 1024:
        return None
    Cursor = 0
    Values: list[str | FormulaAtom] = []
    while Cursor < len(Source):
        Match = KTokenPattern.match(Source, Cursor)
        if Match is None or len(Values) >= 128:
            return None
        Cursor = Match.end()
        if Match.lastgroup == "space":
            continue
        TextValue = Match.group()
        if Match.lastgroup == "operator":
            Values.append(TextValue)
        elif Match.lastgroup == "name":
            Values.append(FormulaAtom(TextValue))
        else:
            UnitStart = Cursor
            while UnitStart < len(Source) and Source[UnitStart] in " \t":
                UnitStart += 1
            UnitMatch = KNamePattern.match(Source, UnitStart)
            UnitName = UnitMatch.group() if UnitMatch is not None else ""
            if UnitMatch is not None and UnitName in KFormulaUnits:
                Cursor = UnitMatch.end()
                Display = f"{TextValue} {UnitName}"
            else:
                UnitName, Display = "", TextValue
            Factor, Dimension = KFormulaUnits[UnitName]
            Magnitude = float(TextValue) * Factor
            if not IsFinite(Magnitude):
                return None
            Values.append(FormulaAtom(Display, (Magnitude, Dimension)))
    return tuple(Values)
