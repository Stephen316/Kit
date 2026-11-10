# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import Items, ParamCatalog
from convert.adapters.freecad.EditRead.Formula.EditFormula import ReadEditFormula
from convert.adapters.freecad.EditRead.Formula.SheetLayout import CheckSheetShape
from convert.adapters.freecad.EditRead.XmlField import (
    CheckEditExpr,
    CheckNoEditExpr,
    EditChild,
)
from convert.adapters.freecad.LiteralQuantity import IsLiteralQty
from convert.adapters.freecad.Native import NativeObject
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.records.RecordParameter import Parameter
from interchange.serialization.EncodeData import ToData


# cell addresses and aliases must be unique before direct expression references are resolved
def EditCells(Sheet: NativeObject, IsLocal: bool) -> dict[str, Element]:
    Cells = EditChild(Sheet, "cells", "Spreadsheet::PropertySheet", "Cells")
    Records = Cells.findall("./Cell")
    if IsLocal:
        Links = Cells.findall("./XLinks")
        if (
            Cells.get("xlink") != "1"
            or len(Links) != 1
            or len(Links[0])
            or Links[0].get("count") != "0"
            or len(Cells) != len(Records) + 1
        ):
            raise ValueError("FreeCAD editable spreadsheet links are no longer local")
    Addresses = [Value.get("address") for Value in Records]
    if (
        Cells.get("Count") != str(len(Records))
        or not all(Addresses)
        or len(set(Addresses)) != len(Addresses)
    ):
        raise ValueError("FreeCAD editable spreadsheet cell addresses are ambiguous")
    Aliased = [(Alias, Value) for Value in Records if (Alias := Value.get("alias"))]
    ByAlias = dict(Aliased)
    if len(ByAlias) != len(Aliased):
        raise ValueError("FreeCAD editable spreadsheet aliases are ambiguous")
    return ByAlias


# the authored cell and persisted evaluated distance must corroborate the same quantity
def ReadCellText(
    Cells: dict[str, Element],
    Alias: str,
    KindValue: ValueKind,
    Expected: float,
    UnitName: str,
) -> str:
    CellValue = Cells.get(Alias)
    Content = "" if CellValue is None else CellValue.get("content", "")
    if not Content.startswith("=") or not IsLiteralQty(
        Content[1:], KindValue, Expected, UnitName
    ):
        raise ValueError(
            f"FreeCAD editable spreadsheet alias {Alias} does not match the saved quantity"
        )
    return Content[1:]


# the original parameter catalog identifies the exact live distance and unchanged zero taper
def ReadEditText(
    Objects: tuple[NativeObject, ...],
    Feature: NativeObject,
    DocValue: CadDocument,
    Definition: DistanceExtrude,
    DepthMm: float,
    StrictLayout: bool = False,
) -> tuple[str, tuple[Parameter, ...]]:
    Catalog = ParamCatalog(Items(ToData(DocValue.parameters)))
    Alias = Catalog.Aliases.get(Definition.AlongParameterId)
    if Alias is None:
        raise ValueError("FreeCAD editable depth has no original parameter alias")
    CheckEditExpr(Feature, "LengthFwd", f"Parameters.{Alias}")
    Sheet = next((Value for Value in Objects if Value.name == "Parameters"), None)
    if Sheet is None or Sheet.type_id != "Spreadsheet::Sheet":
        raise ValueError("FreeCAD editable extrusion parameters sheet is missing")
    CheckNoEditExpr(Sheet)
    DepthParam = next(
        (
            Param
            for Param in DocValue.parameters
            if Param.id == Definition.AlongParameterId
        ),
        None,
    )
    if DepthParam is None:
        raise ValueError("FreeCAD editable spreadsheet depth parameter is missing")
    Expression = DepthParam.expression
    IsLinked = Expression is not None and bool(Expression.parameter_ids)
    Cells = EditCells(Sheet, IsLinked or StrictLayout)
    if StrictLayout:
        CheckSheetShape(Sheet, Cells, Catalog)
    if Definition.TaperParameterId is not None:
        TaperAlias = Catalog.Aliases.get(Definition.TaperParameterId)
        if TaperAlias is None:
            raise ValueError("FreeCAD editable taper has no original parameter alias")
        _ = ReadCellText(Cells, TaperAlias, ValueKind.KAngle, 0.0, "rad")
    if IsLinked:
        if set(Cells) != set(Catalog.Aliases.values()):
            raise ValueError(
                "FreeCAD editable spreadsheet formula alias inventory changed"
            )
        Parameters = tuple(
            Param
            for Param in DocValue.parameters
            if Param.id != Definition.TaperParameterId
        )
        return ReadEditFormula(
            Cells, Catalog.Aliases, Parameters, DepthParam.id, DepthMm
        )
    return ReadCellText(Cells, Alias, ValueKind.KLength, DepthMm, "mm"), ()
