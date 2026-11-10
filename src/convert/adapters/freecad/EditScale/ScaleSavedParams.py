# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace
from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import ParamCatalog
from convert.adapters.freecad.EditRead.EditSheet import EditCells
from convert.adapters.freecad.EditRead.Formula.SavedQuantity import KeepQuantity
from convert.adapters.freecad.EditRead.Formula.SheetLayout import CheckSheetShape
from convert.adapters.freecad.EditRead.XmlField import KEditNumber
from convert.adapters.freecad.LiteralQuantity import IsLiteralQty
from convert.adapters.freecad.Native import NativeObject
from convert.geometry.Formula.Arithmetic import (
    EvalFormula,
    IsLiteralExpr,
    ReadFormula,
)
from convert.geometry.Formula.FormulaUnits import GetQuantity
from interchange.records.RecordParameter import Expression, Parameter


# only closed literal inputs can override the corresponding neutral scale controls
def ReadScaleScalar(Param: Parameter, Content: str) -> Parameter:
    TextValue = Content.removeprefix("=")
    Formula = ReadFormula(TextValue) if len(TextValue) <= 128 else None
    if (
        Formula is None
        or not IsLiteralExpr(Formula)
        or (Content == TextValue and KEditNumber.fullmatch(TextValue) is None)
        or (Quantity := EvalFormula(Formula, {})) is None
    ):
        raise ValueError("FreeCAD editable Scale sheet input is not a literal quantity")
    Value = KeepQuantity(Param.value, Quantity)
    if not IsLiteralQty(TextValue, Value.kind, Value.value, Value.unit):
        raise ValueError("FreeCAD editable Scale sheet literal has invalid units")
    if Value is Param.value:
        return Param
    Previous = Param.expression
    ExpressionValue = (
        Replace(Previous, source=TextValue)
        if Previous is not None
        else Expression(TextValue, language="freecad")
    )
    return Replace(Param, value=Value, expression=ExpressionValue)


# native cell framing keeps formatting records from introducing additional authored state
def ReadScaleCells(Sheet: NativeObject, Catalog: ParamCatalog) -> dict[str, Element]:
    Cells = EditCells(Sheet, True)
    CheckSheetShape(Sheet, Cells, Catalog)
    Container = Sheet.properties["cells"][0]
    XLinks = Container.find("XLinks")
    if (
        Container.attrib.keys() != {"Count", "xlink"}
        or XLinks is None
        or XLinks.attrib != {"count": "0"}
        or any(
            len(RowValue)
            or RowValue.attrib.keys()
            != (
                {"address", "content", "alias"}
                if RowValue.get("alias")
                else {"address", "content"}
            )
            for RowValue in Container.findall("Cell")
        )
    ):
        raise ValueError("FreeCAD editable Scale cell metadata changed")
    return Cells


# all noneditable rows retain the original authored quantity or exact source expression
def ReadScaleParams(
    Sheet: NativeObject,
    Expected: NativeObject,
    Catalog: ParamCatalog,
    Parameters: tuple[Parameter, ...],
    Editable: set[str],
) -> tuple[Parameter, ...]:
    Cells = ReadScaleCells(Sheet, Catalog)
    Original = ReadScaleCells(Expected, Catalog)
    Result: list[Parameter] = []
    for Param in Parameters:
        Alias = Catalog.Aliases[Param.id]
        Before = Original[Alias].get("content", "")
        After = Cells[Alias].get("content", "")
        if Param.id in Editable:
            Param = ReadScaleScalar(Param, After)
        elif Before != After and (
            GetQuantity(Param.value) is None
            or ReadScaleScalar(Param, Before).value
            != ReadScaleScalar(Param, After).value
        ):
            raise ValueError("FreeCAD editable Scale has an unbound parameter edit")
        Result.append(Param)
    return tuple(Result)
