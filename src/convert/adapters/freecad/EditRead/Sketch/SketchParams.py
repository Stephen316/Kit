# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from dataclasses import replace as Replace

from convert.adapters.freecad.Archive import ParamCatalog
from convert.adapters.freecad.EditRead.EditSheet import EditCells
from convert.adapters.freecad.EditRead.Formula.SavedLiteral import ReadSavedLeaf
from convert.adapters.freecad.EditRead.Formula.SavedQuantity import (
    KeepQuantity,
    KCanonicalUnits,
)
from convert.adapters.freecad.EditRead.Formula.SheetLayout import CheckSheetShape
from convert.adapters.freecad.Native import NativeObject
from convert.geometry.Formula.FormulaUnits import GetQuantity, IsMatchingQty
from interchange.records.RecordParameter import Parameter


# only driving dimensions may take their new literal values from the worksheet
def ReadSketchVals(
    Sheet: NativeObject,
    Catalog: ParamCatalog,
    Original: tuple[Parameter, ...],
    Drivers: Mapping[str, bool],
) -> dict[str, Parameter]:
    Cells = EditCells(Sheet, True)
    CheckSheetShape(Sheet, Cells, Catalog)
    Result: dict[str, Parameter] = {}
    for ParamValue in Original:
        Content = Cells[Catalog.Aliases[ParamValue.id]].get("content", "")
        if not Content.startswith("="):
            raise ValueError(
                "FreeCAD editable sketch dimension has no live worksheet quantity"
            )
        Updated = ReadSavedLeaf(ParamValue, Content[1:])
        if not Drivers[ParamValue.id] and Updated is not ParamValue:
            raise ValueError(
                "FreeCAD editable sketch reference worksheet value was changed"
            )
        Result[ParamValue.id] = Updated
    return Result


# measured reference dimensions follow corroborated geometry instead of stale worksheet values
def KeepSketchRef(ParamValue: Parameter, Measure: float) -> Parameter:
    Quantity = GetQuantity(ParamValue.value)
    Expression = ParamValue.expression
    if Quantity is None or Expression is None:
        raise ValueError(
            "FreeCAD editable sketch reference dimension has no typed quantity"
        )
    NewQuantity = (Measure, Quantity[1])
    if IsMatchingQty(NewQuantity, ParamValue.value):
        return ParamValue
    UnitValue = KCanonicalUnits[Quantity[1]]
    return Replace(
        ParamValue,
        value=KeepQuantity(ParamValue.value, NewQuantity),
        expression=Replace(Expression, source=f"{Measure:.17g} {UnitValue}"),
    )
