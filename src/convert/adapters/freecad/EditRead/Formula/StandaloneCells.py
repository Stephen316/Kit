# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.Formula.FormulaValue import EvalSavedRow
from convert.adapters.freecad.EditRead.Formula.SavedLiteral import ReadSavedLeaf
from convert.adapters.freecad.FormulaSheet.FormulaClosure import CloseFormulas
from convert.adapters.freecad.FormulaSheet.FormulaPlans import (
    FormulaPlan,
    ReadFusionPlan,
)
from convert.geometry.Formula.Arithmetic import IsLiteralFormula, ReadFormula
from interchange.records.RecordParameter import Parameter


# independent sheet formulas can have several roots but still require a complete verified graph
def ReadSheetPlans(
    Parameters: dict[str, Parameter], Aliases: dict[str, str]
) -> tuple[dict[str, FormulaPlan], tuple[str, ...]]:
    Plans: dict[str, FormulaPlan] = {}
    for Identity, Param in Parameters.items():
        Expression = Param.expression
        if Param.owner_id or Expression is None or Expression.language != "fusion":
            raise ValueError(
                "FreeCAD editable spreadsheet has a non-Fusion parameter scope"
            )
        PlanValue = ReadFusionPlan(Param, Parameters, Aliases)
        if PlanValue is None:
            raise ValueError(
                "FreeCAD editable spreadsheet snapshot formula is unresolved"
            )
        Plans[Identity] = PlanValue
    Ordered = CloseFormulas(Plans)
    if Ordered.keys() != Plans.keys():
        raise ValueError(
            "FreeCAD editable spreadsheet formula references contain a cycle"
        )
    return Plans, tuple(Ordered)


# independent literal drivers update before any formula that consumes their typed value
def ReadSavedSheet(
    Cells: Mapping[str, Element],
    Aliases: dict[str, str],
    Parameters: tuple[Parameter, ...],
) -> tuple[Parameter, ...]:
    Original = {Param.id: Param for Param in Parameters}
    Expected = {Aliases.get(Identity) for Identity in Original}
    if (
        len(Original) != len(Parameters)
        or None in Expected
        or len(Expected) != len(Original)
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet parameter aliases are missing or ambiguous"
        )
    Plans, Order = ReadSheetPlans(Original, Aliases)
    Current, Changes = dict(Original), set()
    for Identity in Order:
        Param, PlanValue = Original[Identity], Plans[Identity]
        Alias = Aliases[Identity]
        CellValue = Cells.get(Alias)
        Content = "" if CellValue is None else CellValue.get("content", "")
        if not Content.startswith("="):
            raise ValueError(
                f"FreeCAD editable spreadsheet alias {Alias} has no live content"
            )
        Literal = None if PlanValue.References else ReadFormula(PlanValue.Content)
        if Literal is not None and IsLiteralFormula(Literal):
            Updated = ReadSavedLeaf(Param, Content[1:])
        else:
            Updated = EvalSavedRow(
                Param, PlanValue, Content[1:], Current, Aliases, Changes, None
            )
        Current[Identity] = Updated
        if Updated is not Param:
            Changes.add(Identity)
    return tuple(Current[Param.id] for Param in Parameters) if Changes else Parameters
