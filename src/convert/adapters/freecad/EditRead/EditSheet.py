# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import Items, ParamCatalog
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
from interchange.serialization.EncodeData import ToData


# cell addresses and aliases must be unique before direct expression references are resolved
def EditCells(Sheet: NativeObject) -> dict[str, Element]:
    Cells = EditChild(Sheet, "cells", "Spreadsheet::PropertySheet", "Cells")
    Records = Cells.findall("./Cell")
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
) -> str:
    Catalog = ParamCatalog(Items(ToData(DocValue.parameters)))
    Alias = Catalog.Aliases.get(Definition.AlongParameterId)
    if Alias is None:
        raise ValueError("FreeCAD editable depth has no original parameter alias")
    CheckEditExpr(Feature, "LengthFwd", f"Parameters.{Alias}")
    Sheet = next((Value for Value in Objects if Value.name == "Parameters"), None)
    if Sheet is None or Sheet.type_id != "Spreadsheet::Sheet":
        raise ValueError("FreeCAD editable extrusion parameters sheet is missing")
    CheckNoEditExpr(Sheet)
    Cells = EditCells(Sheet)
    if Definition.TaperParameterId is not None:
        TaperAlias = Catalog.Aliases.get(Definition.TaperParameterId)
        if TaperAlias is None:
            raise ValueError("FreeCAD editable taper has no original parameter alias")
        ReadCellText(Cells, TaperAlias, ValueKind.KAngle, 0.0, "rad")
    return ReadCellText(Cells, Alias, ValueKind.KLength, DepthMm, "mm")
