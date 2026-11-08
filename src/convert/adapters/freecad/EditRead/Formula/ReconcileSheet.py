# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from dataclasses import replace as Replace
from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import Items, ParamCatalog
from convert.adapters.freecad.EditBinding import ReadEditBinding
from convert.adapters.freecad.EditRead.EditSheet import EditCells
from convert.adapters.freecad.EditRead.Formula.SheetLayout import CheckSheetLayout
from convert.adapters.freecad.EditRead.Formula.SheetScope import ReadSheetObject
from convert.adapters.freecad.EditRead.Formula.StandaloneCells import ReadSavedSheet
from convert.adapters.freecad.FormulaSheet.SheetBinding import KFormulaSheetBinding
from convert.adapters.freecad.FormulaSheet.SheetScope import CanEditSheet
from interchange.document.models.DocumentModel import CadDocument


# bound spreadsheets can replace only the parameter values verified against their source graph
def ReconcileSheet(
    DocValue: CadDocument, Manifest: Mapping[str, object], RootValue: Element
) -> CadDocument:
    Binding = ReadEditBinding(RootValue, KFormulaSheetBinding)
    if Binding is None:
        return DocValue
    Rows = Items(Manifest.get("parameters", []))
    Catalog = ParamCatalog(Rows)
    if Binding != "Parameters" or not CanEditSheet(
        Manifest, Rows, Catalog.FusionExpressions
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet binding disagrees with its source"
        )
    Sheet = ReadSheetObject(RootValue)
    Cells = EditCells(Sheet, True)
    CheckSheetLayout(Sheet, Cells, Catalog)
    Parameters = ReadSavedSheet(Cells, Catalog.Aliases, DocValue.parameters)
    if Parameters is DocValue.parameters:
        return DocValue
    return Replace(DocValue, parameters=Parameters)
