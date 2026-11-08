# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import Items, ParamCatalog
from convert.adapters.freecad.EditableRev import EditRevolve
from convert.adapters.freecad.EditRead.EditSheet import EditCells
from convert.adapters.freecad.EditRead.Formula.SheetScaffold import (
    CheckProperties,
    CheckSheetDeps,
)
from convert.adapters.freecad.EditRead.Formula.SheetScope import KSheetFields
from convert.adapters.freecad.EditRead.XmlField import EditChild
from convert.adapters.freecad.Native import NativeObject
from convert.geometry.Formula.Arithmetic import (
    EvalFormula,
    IsLiteralFormula,
    ReadFormula,
)
from convert.geometry.Formula.FormulaUnits import MatchQuantity
from interchange.records.RecordParameter import Parameter
from interchange.serialization.EncodeData import ToData


# stable rows keep every authored angle on its original editable spreadsheet alias
def ReadRevCells(
    Sheet: NativeObject, Parameters: tuple[Parameter, ...], Aliases: dict[str, str]
) -> dict[str, Element]:
    CheckProperties(Sheet, KSheetFields)
    CheckSheetDeps(Sheet, ())
    if Sheet.extensions or Sheet.transient_properties:
        raise ValueError("FreeCAD editable Revolve spreadsheet extension changed")
    ByAlias = EditCells(Sheet, True)
    Cells = EditChild(Sheet, "cells", "Spreadsheet::PropertySheet", "Cells")
    ByAddress = {Value.get("address"): Value for Value in Cells.findall("./Cell")}
    if set(ByAlias) != set(Aliases.values()) or len(ByAddress) != 2 * len(Parameters):
        raise ValueError("FreeCAD editable Revolve spreadsheet alias inventory changed")
    for Index, Param in enumerate(Parameters, 1):
        Label = ByAddress.get(f"A{Index}")
        Alias = ByAlias[Aliases[Param.id]]
        if (
            Label is None
            or Label.get("content") != f"'{Param.name}"
            or Label.get("alias")
            or Alias.get("address") != f"B{Index}"
            or len(Label)
            or len(Alias)
        ):
            raise ValueError("FreeCAD editable Revolve spreadsheet row binding changed")
    return ByAlias


# a finite literal angle is authoritative only within its original physical dimension
def ReadRevLiteral(Content: str, Param: Parameter) -> tuple[float, str]:
    SourceText = Content[1:] if Content.startswith("=") else ""
    Formula = ReadFormula(SourceText)
    if Formula is None or not IsLiteralFormula(Formula):
        raise ValueError("FreeCAD editable Revolve angle cell is not a literal")
    Quantity = EvalFormula(Formula, {})
    if Quantity is None or Quantity[1] != (0, 1):
        raise ValueError("FreeCAD editable Revolve angle cell has the wrong unit")
    if MatchQuantity(Quantity, Param.value):
        return float(Param.value.value), SourceText
    return Quantity[0], SourceText


# mirrored and independently authored angle cells require different saved dependencies
def ReadRevSheet(
    Sheet: NativeObject, Parameters: tuple[Parameter, ...], PlanValue: EditRevolve
) -> tuple[dict[str, str], float, float | None, str, str | None]:
    Catalog = ParamCatalog(Items(ToData(Parameters)))
    Aliases = Catalog.Aliases
    Cells = ReadRevCells(Sheet, Parameters, Aliases)
    ByParam = {Value.id: Value for Value in Parameters}
    AlongId, AgainstId = PlanValue.AngleParamId, PlanValue.AgainstParamId
    AlongAlias = Aliases[AlongId]
    Along, AlongText = ReadRevLiteral(
        Cells[AlongAlias].get("content", ""), ByParam[AlongId]
    )
    if AgainstId is None:
        return Aliases, Along, None, AlongText, None
    Content = Cells[Aliases[AgainstId]].get("content", "")
    if PlanValue.AngleScale == 2.0:
        if Content != f"={AlongAlias}":
            raise ValueError(
                "FreeCAD editable Revolve mirrored angle cell binding changed"
            )
        return Aliases, Along, Along, AlongText, AlongText
    Against, AgainstText = ReadRevLiteral(Content, ByParam[AgainstId])
    return Aliases, Along, Against, AlongText, AgainstText
