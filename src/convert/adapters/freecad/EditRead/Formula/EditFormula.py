# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.Formula.FormulaOrder import ReadPlanOrder
from convert.adapters.freecad.EditRead.Formula.FormulaValue import EvalSavedRow
from convert.adapters.freecad.EditRead.Formula.SavedLiteral import ReadSavedLeaf
from interchange.records.RecordParameter import Parameter


# saved leaves and reevaluated dependents enter the document as one coherent set of edits
def ReadEditFormula(
    Cells: dict[str, Element],
    Aliases: dict[str, str],
    Parameters: tuple[Parameter, ...],
    DepthId: str,
    DepthMm: float,
) -> tuple[str, tuple[Parameter, ...]]:
    Original = {Param.id: Param for Param in Parameters}
    if len(Original) != len(Parameters):
        raise ValueError(
            "FreeCAD editable spreadsheet parameter identities are ambiguous"
        )
    Plans, Order = ReadPlanOrder(Original, Aliases, DepthId)
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
        SourceText = Content[1:]
        if PlanValue.References:
            Updated = EvalSavedRow(
                Param,
                PlanValue,
                SourceText,
                Current,
                Aliases,
                Changes,
                DepthMm if Identity == DepthId else None,
            )
        else:
            Updated = ReadSavedLeaf(Param, SourceText)
        Current[Identity] = Updated
        if Updated is not Param:
            Changes.add(Identity)
    Expression = Original[DepthId].expression
    if Expression is None or not Expression.parameter_ids:
        raise ValueError("FreeCAD editable spreadsheet depth formula is missing")
    return Expression.source, tuple(
        Current[Param.id] for Param in Parameters if Param.id in Changes
    )
