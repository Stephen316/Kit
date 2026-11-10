# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.geometry.Formula.Arithmetic import EvalFormula, ReadFormula
from convert.geometry.Formula.FormulaUnits import IsMatchingQty
from interchange.enums.EnumValues import ParameterRole
from interchange.records.RecordParameter import Parameter


# only native unbound user names have proven standalone formula visibility
def IsUserParam(ParamValue: Parameter) -> bool:
    Attributes = ParamValue.attributes
    return (
        not ParamValue.owner_id
        and ParamValue.role == ParameterRole.KDriving
        and Attributes.get("fusion.native_role") == "User Parameter"
        and "fusion.binding_id" in Attributes
        and Attributes["fusion.binding_id"] is None
        and "fusion.owner_object_id" not in Attributes
    )


# an owned model parameter can refer to user names without becoming globally visible
def IsFormulaOwner(ParamValue: Parameter) -> bool:
    Attributes = ParamValue.attributes
    return isinstance(Attributes.get("fusion.binding_id"), int) and isinstance(
        Attributes.get("fusion.owner_object_id"), int
    )


# cached typed values independently constrain each candidate dependency expression
def GetFormulaGraph(Parameters: tuple[Parameter, ...]) -> dict[str, tuple[str, ...]]:
    Users = {Param.name: Param for Param in Parameters if IsUserParam(Param)}
    Quantities = {NameValue: Param.value for NameValue, Param in Users.items()}
    Graph: dict[str, tuple[str, ...]] = {}
    for Param in Parameters:
        Expression = Param.expression
        if Expression is None:
            if Param.name in Users:
                Graph[Param.id] = ()
            continue
        if (
            Expression.language != "fusion"
            or Expression.parameter_ids
            or (Param.name not in Users and not IsFormulaOwner(Param))
        ):
            continue
        Formula = ReadFormula(Expression.source)
        if Formula is None or any(
            NameValue not in Users or Users[NameValue].id == Param.id
            for NameValue in Formula.Names
        ):
            continue
        Result = EvalFormula(Formula, Quantities)
        if Result is not None and IsMatchingQty(Result, Param.value):
            Graph[Param.id] = tuple(Users[NameValue].id for NameValue in Formula.Names)
    return Graph
