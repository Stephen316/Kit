# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace

from convert.geometry.Formula.FormulaUnits import (
    GetQuantity,
    KDimension,
    KFormulaUnits,
    KQuantity,
)
from interchange.enums.EnumValues import ValueKind
from interchange.records.RecordParameter import ParameterValue

# exact canonical units avoid a roundtrip through an inexact source conversion factor
KCanonicalUnits: dict[KDimension, str] = {(1, 0): "mm", (0, 1): "rad", (0, 0): ""}


# preserve the original storage units whenever they reproduce the exact edited quantity
def KeepQuantity(Original: ParameterValue, Quantity: KQuantity) -> ParameterValue:
    Stored = GetQuantity(Original)
    if Stored == Quantity:
        return Original
    if Stored is None or Stored[1] != Quantity[1]:
        raise ValueError(
            "FreeCAD editable spreadsheet quantity changed physical dimensions"
        )
    Magnitude, Dimension = Quantity
    UnitName = Original.unit
    Factor = KFormulaUnits[UnitName][0]
    Numeric = Magnitude / Factor
    if Numeric * Factor != Magnitude:
        Numeric, UnitName = Magnitude, KCanonicalUnits[Dimension]
    if Original.kind == ValueKind.KInteger:
        if not Numeric.is_integer():
            raise ValueError(
                "FreeCAD editable spreadsheet value is no longer an integer"
            )
        return Replace(Original, value=int(Numeric), unit=UnitName)
    return Replace(Original, value=Numeric, unit=UnitName)
