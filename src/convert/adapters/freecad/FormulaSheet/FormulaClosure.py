from collections import deque as MakeDeque
from typing import Mapping

from convert.adapters.freecad.FormulaSheet.FormulaPlans import (
    FormulaPlan,
    ReadFusionPlan,
    ReadFusionRows,
)


# dependency closure keeps unsupported inputs and cyclic subgraphs on their carrier path
def CloseFormulas(Plans: dict[str, FormulaPlan]) -> dict[str, str]:
    Pending: dict[str, int] = {}
    Dependents: dict[str, list[str]] = {}
    Ready: MakeDeque[str] = MakeDeque()
    for Identity, PlanValue in Plans.items():
        Pending[Identity] = len(PlanValue.References)
        if not PlanValue.References:
            Ready.append(Identity)
        for Reference in PlanValue.References:
            Dependents.setdefault(Reference, []).append(Identity)
    Result: dict[str, str] = {}
    while Ready:
        Identity = Ready.popleft()
        Result[Identity] = Plans[Identity].Content
        for Dependent in Dependents.get(Identity, ()):
            Pending[Dependent] -= 1
            if Pending[Dependent] == 0:
                Ready.append(Dependent)
    return Result


# one bounded graph pass lets cell generation and transfer reporting share the same decision
def BuildFusionExpr(
    Parameters: list[dict[str, object]], Aliases: Mapping[str, str]
) -> dict[str, str]:
    ParameterRows = ReadFusionRows(Parameters)
    Plans: dict[str, FormulaPlan] = {}
    for Identity, Value in ParameterRows.items():
        PlanValue = ReadFusionPlan(Value, ParameterRows, Aliases)
        if PlanValue is not None:
            Plans[Identity] = PlanValue
    return CloseFormulas(Plans)
