# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from graphlib import CycleError, TopologicalSorter as SortTopology

from convert.adapters.freecad.FormulaSheet.FormulaPlans import (
    FormulaPlan,
    ReadFusionPlan,
)
from interchange.records.RecordParameter import Parameter


# only a verified snapshot graph can identify every locally editable cell
def ReadPlanOrder(
    Parameters: dict[str, Parameter], Aliases: dict[str, str], DepthId: str
) -> tuple[dict[str, FormulaPlan], tuple[str, ...]]:
    Pending = [DepthId]
    Plans: dict[str, FormulaPlan] = {}
    while Pending:
        Identity = Pending.pop()
        if Identity in Plans:
            continue
        Param = Parameters.get(Identity)
        Expression = None if Param is None else Param.expression
        if (
            Param is None
            or Expression is None
            or Expression.language != "fusion"
            or (Identity != DepthId and Param.owner_id)
            or Identity not in Aliases
        ):
            raise ValueError(
                "FreeCAD editable spreadsheet has an invalid Fusion parameter scope"
            )
        PlanValue = ReadFusionPlan(Param, Parameters, Aliases)
        if PlanValue is None:
            raise ValueError(
                "FreeCAD editable spreadsheet snapshot formula is unresolved"
            )
        Plans[Identity] = PlanValue
        Pending.extend(PlanValue.References)
    if Plans.keys() != Parameters.keys():
        raise ValueError(
            "FreeCAD editable spreadsheet parameters extend outside the depth formula"
        )
    try:
        Order = tuple(
            SortTopology(
                {
                    Identity: PlanValue.References
                    for Identity, PlanValue in Plans.items()
                }
            ).static_order()
        )
    except CycleError as ErrorInfo:
        raise ValueError(
            "FreeCAD editable spreadsheet formula references contain a cycle"
        ) from ErrorInfo
    return Plans, Order
