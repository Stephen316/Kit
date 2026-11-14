from typing import Mapping

from convert.adapters.solidworks.core.Native import NativeEquation
from interchange.records.RecordParameter import Expression


def EquationData(
    Equation: NativeEquation,
    GlobalIds: Mapping[str, str],
    DimensionIds: Mapping[tuple[str, str], str | None],
) -> tuple[Expression, dict[str, object]]:
    BoundIds, Unresolved = EquationLinks(Equation.references, GlobalIds, DimensionIds)
    Evidence: dict[str, object] = {
        "equation_source": Equation.source,
        "equation_configuration_id": Equation.configuration_id,
    }
    if Unresolved:
        Evidence["unresolved_equation_references"] = Unresolved
    return Expression(Equation.rhs, BoundIds, "solidworks"), Evidence


def EquationLinks(
    References: tuple[str, ...],
    GlobalIds: Mapping[str, str],
    DimensionIds: Mapping[tuple[str, str], str | None],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    BoundIds: list[str] = []
    Unresolved: list[str] = []
    for Reference in References:
        DimensionName, Separator, FeatureName = Reference.partition("@")
        ParameterId = (
            DimensionIds.get((FeatureName, DimensionName))
            if Separator
            else GlobalIds.get(Reference)
        )
        if ParameterId is None:
            Unresolved.append(Reference)
        else:
            BoundIds.append(ParameterId)
    return tuple(BoundIds), tuple(Unresolved)
