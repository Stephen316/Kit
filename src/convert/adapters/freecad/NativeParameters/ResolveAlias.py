from collections.abc import Mapping
from dataclasses import replace as Replace
from re import compile as CompileRegex

from convert.adapters.freecad.NativeParameters.ReadEvidence import HasSavedValue
from convert.Geometry.Formula.FormulaUnits import GetQuantity, IsMatchingQty
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter

# only object qualified direct references have a complete native ownership rule in this slice
KDirectAlias = CompileRegex(
    r"=?[ \t]*(?P<sheet>[A-Za-z_][A-Za-z_0-9]{0,127})"
    + r"\.(?P<alias>[A-Za-z_][A-Za-z_0-9]{0,127})"
)


# dependency links require both exact native ownership and corroborated current physical quantities
def ResolveAlias(
    Param: Parameter, Aliases: Mapping[tuple[str, str], Parameter]
) -> tuple[Parameter, str]:
    Expression = Param.expression
    if (
        Expression is None
        or Expression.language != "freecad"
        or Expression.parameter_ids
    ):
        return Param, ""
    if len(Expression.source) > 1024:
        return Param, "expression_limit"
    Match = KDirectAlias.fullmatch(Expression.source.strip())
    if Match is None:
        return Param, "unsupported_reference"
    Target = Aliases.get((Match["sheet"], Match["alias"]))
    if Target is None:
        return Param, "missing_or_ambiguous_alias"
    if not HasSavedValue(Param):
        return Param, "unverified_native_value"
    Quantity = GetQuantity(Target.value)
    if (
        Quantity is None
        or not IsMatchingQty(Quantity, Param.value)
        or (
            Param.value.kind == ValueKind.KInteger
            and Target.value.value != Param.value.value
        )
    ):
        return Param, "quantity_mismatch"
    return (
        Replace(Param, expression=Replace(Expression, parameter_ids=(Target.id,))),
        "",
    )
