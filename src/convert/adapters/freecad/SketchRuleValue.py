# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping

from convert.adapters.base.WriteValidate import IsObjectMap
from convert.adapters.freecad.Protocol import KRuleValueKindByCode
from convert.geometry.Formula.FormulaUnits import KFormulaUnits


# unsigned source distances still need the direction of their ordered point references
def GetRuleSign(KindValue: str, Attributes: Mapping[str, object]) -> int:
    if (
        KindValue in {"distance_x", "distance_y"}
        and Attributes.get("fusion.signed_distance_multiplier") == -1
    ):
        return -1
    return 1


# serialized sketch values use canonical solver units before expressions are evaluated
def GetRuleValue(CodeValue: int, Parameter: object, Value: float) -> float:
    Expected = KRuleValueKindByCode.get(CodeValue)
    if Expected is None or not IsObjectMap(Parameter):
        return Value
    DataValue = Parameter.get("value")
    if not IsObjectMap(DataValue):
        return Value
    UnitValue = DataValue.get("unit")
    SourceUnit = KFormulaUnits.get(UnitValue) if isinstance(UnitValue, str) else None
    TargetUnit = KFormulaUnits.get(Expected[1])
    if SourceUnit is None or TargetUnit is None or SourceUnit[1] != TargetUnit[1]:
        raise ValueError("FreeCAD sketch constraint parameter unit is unsupported")
    return Value * SourceUnit[0] / TargetUnit[0]
