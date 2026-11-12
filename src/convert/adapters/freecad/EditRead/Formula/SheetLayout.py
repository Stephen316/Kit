from collections.abc import Mapping
from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import ParamCatalog, TextAction
from convert.adapters.freecad.EditRead.XmlField import CheckNoEditExpr, EditChild
from convert.adapters.freecad.Native import NativeObject


# the full worksheet grid prevents untracked cells from being discarded on import
def CheckSheetShape(
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
    for Index, RowValue in enumerate(Catalog.Parameters, start=1):
        ParamId = TextAction(RowValue.get("id"), f"parameter_{Index}")
        ExpectedLabels[f"A{Index}"] = "'" + TextAction(RowValue.get("name"), ParamId)
        ExpectedAddresses[Catalog.Aliases[ParamId]] = f"B{Index}"
    if (
        Labels != ExpectedLabels
        or {Alias: CellValue.get("address") for Alias, CellValue in Cells.items()}
        != ExpectedAddresses
    ):
        raise ValueError("FreeCAD editable spreadsheet cell layout changed")
