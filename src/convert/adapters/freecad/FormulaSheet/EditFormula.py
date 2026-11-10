# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping

from convert.adapters.freecad.FormulaSheet.FormulaClosure import CloseFormulas
from convert.adapters.freecad.FormulaSheet.FormulaPlans import (
    FormulaPlan,
    ReadFusionPlan,
)
from convert.geometry.Formula.Arithmetic import IsLiteralExpr, ReadFormula
from interchange.records.RecordParameter import Parameter


# the editable feature requires a proven dependency chain with writable literal inputs
def IsEditFormula(
    DepthId: str, TaperId: str | None, Parameters: Mapping[str, Parameter]
) -> bool:
    Aliases = {
        Identity: f"edit_parameter_{Index}" for Index, Identity in enumerate(Parameters)
    }
    Pending = [DepthId]
    Plans: dict[str, FormulaPlan] = {}
    while Pending:
        Identity = Pending.pop()
        if Identity in Plans:
            continue
        Param = Parameters.get(Identity)
        if Param is None or (Identity != DepthId and Param.owner_id):
            return False
        Expression = Param.expression
        if Expression is None or Expression.language != "fusion":
            return False
        PlanValue = ReadFusionPlan(Param, Parameters, Aliases)
        if PlanValue is None:
            return False
        if not PlanValue.References:
            Parsed = ReadFormula(Expression.source)
            if Parsed is None or not IsLiteralExpr(Parsed):
                return False
        Plans[Identity] = PlanValue
        Pending.extend(PlanValue.References)
    Expected = set(Plans)
    if TaperId is not None:
        Expected.add(TaperId)
    return (
        Expected == set(Parameters)
        and bool(Plans[DepthId].References)
        and DepthId in CloseFormulas(Plans)
    )
