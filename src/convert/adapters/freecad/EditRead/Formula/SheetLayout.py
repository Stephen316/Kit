# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import ParamCatalog, TextAction
from convert.adapters.freecad.EditRead.XmlField import CheckNoEditExpr, EditChild
from convert.adapters.freecad.Native import NativeObject


# the full worksheet grid prevents untracked cells from being discarded on import
def CheckSheetLayout(
    Sheet: NativeObject, Cells: Mapping[str, Element], Catalog: ParamCatalog
) -> None:
    CheckNoEditExpr(Sheet)
    Records = EditChild(Sheet, "cells", "Spreadsheet::PropertySheet", "Cells")
    Labels = {
        Value.get("address"): Value.get("content")
        for Value in Records.findall("Cell")
        if not Value.get("alias")
    }
    ExpectedLabels: dict[str, str] = {}
    ExpectedAddresses: dict[str, str] = {}
    for Index, Row in enumerate(Catalog.Parameters, start=1):
        ParamId = TextAction(Row.get("id"), f"parameter_{Index}")
        ExpectedLabels[f"A{Index}"] = "'" + TextAction(Row.get("name"), ParamId)
        ExpectedAddresses[Catalog.Aliases[ParamId]] = f"B{Index}"
    if (
        Labels != ExpectedLabels
        or {Alias: Cell.get("address") for Alias, Cell in Cells.items()}
        != ExpectedAddresses
    ):
        raise ValueError("FreeCAD editable spreadsheet cell layout changed")
