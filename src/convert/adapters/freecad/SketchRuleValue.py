# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping

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
    if Expected is None or not isinstance(Parameter, Mapping):
        return Value
    DataValue = Parameter.get("value")
    if not isinstance(DataValue, Mapping):
        return Value
    UnitValue = DataValue.get("unit")
    SourceUnit = KFormulaUnits.get(UnitValue) if isinstance(UnitValue, str) else None
    TargetUnit = KFormulaUnits.get(Expected[1])
    if SourceUnit is None or TargetUnit is None or SourceUnit[1] != TargetUnit[1]:
        return Value
    return Value * SourceUnit[0] / TargetUnit[0]
