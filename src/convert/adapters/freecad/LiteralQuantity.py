# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose, isfinite as IsFinite, pi as HalfTurn
from re import compile as CompilePattern

from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceParam import KLengthFactors

# only self contained dimensioned numbers can preserve editable fusion literal controls
KLiteralPattern = CompilePattern(
    r"([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)" r"[ \t]+([a-z]+)"
)

# native degrees and stored radians represent the same literal angle
KAngleFactors = {"deg": HalfTurn / 180.0, "rad": 1.0}


# confirming the typed value prevents mistaking a stale literal for the current control
def IsLiteralQty(
    SourceText: str, KindValue: ValueKind | str, StoredValue: object, StoredUnit: object
) -> bool:
    if (
        not isinstance(SourceText, str)
        or len(SourceText) > 128
        or not isinstance(StoredUnit, str)
        or not isinstance(StoredValue, (float, int))
        or isinstance(StoredValue, bool)
    ):
        return False
    TextValue = SourceText.strip(" \t")
    IsWrapped = TextValue.startswith("-(") and TextValue.endswith(")")
    if IsWrapped:
        TextValue = TextValue[2:-1].strip(" \t")
    Match = KLiteralPattern.fullmatch(TextValue)
    if Match is None or KindValue not in (ValueKind.KLength, ValueKind.KAngle):
        return False
    Factors = KLengthFactors if KindValue == ValueKind.KLength else KAngleFactors
    NumberText, SourceUnit = Match.groups()
    if SourceUnit not in Factors or StoredUnit not in Factors:
        return False
    try:
        Literal = (-1.0 if IsWrapped else 1.0) * float(NumberText) * Factors[SourceUnit]
        Current = StoredValue * Factors[StoredUnit]
    except OverflowError:
        return False
    return (
        IsFinite(Literal)
        and IsFinite(Current)
        and IsClose(Literal, Current, rel_tol=1e-12, abs_tol=0.0)
    )
