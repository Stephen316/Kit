# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.FormulaSheet.EditFormula import IsEditFormula
from convert.adapters.freecad.LiteralQuantity import IsLiteralQty
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# dependent formulas cannot be replaced with writable scalar spreadsheet cells
def IsLiteralParam(Param: Parameter, *, AllowKit: bool = False) -> bool:
    Expression = Param.expression
    Value = Param.value
    return Expression is None or (
        (
            Expression.language in {"fusion", "freecad"}
            or (AllowKit and Expression.language == "kit")
        )
        and not Expression.parameter_ids
        and IsLiteralQty(Expression.source, Value.kind, Value.value, Value.unit)
    )


# the native extrusion owns one signed blind depth and a fixed zero draft
def GetEditDepth(
    FeatureValue: FeatureStep,
    Definition: DistanceExtrude,
    Parameters: tuple[Parameter, ...],
) -> float | None:
    if Definition.SideMode != "one_sided" or any(
        Value is not None
        for Value in (
            Definition.StartOffsetId,
            Definition.AgainstParameterId,
            Definition.SecondTaperId,
        )
    ):
        return None
    Params = {Value.id: Value for Value in Parameters}
    Bindings = {
        Value
        for Value in (Definition.AlongParameterId, Definition.TaperParameterId)
        if Value is not None
    }
    if (
        len(Params) != len(Parameters)
        or len(FeatureValue.parameter_ids) != len(Bindings)
        or set(FeatureValue.parameter_ids) != Bindings
    ):
        return None
    Values = GetDistValues(FeatureValue, Definition, Params)
    TaperId = Definition.TaperParameterId
    DepthId = Definition.AlongParameterId
    if (
        Values.TaperRadians != 0.0
        or (TaperId is not None and not IsLiteralParam(Params[TaperId]))
        or (
            not IsLiteralParam(Params[DepthId])
            and not IsEditFormula(DepthId, TaperId, Params)
        )
    ):
        return None
    return Values.LowerMm if Values.LowerMm < 0.0 else Values.UpperMm
