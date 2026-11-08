# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Iterator
from contextlib import contextmanager as ContextManager
from pathlib import Path as FilePath
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.FormulaSheet.SheetBinding import KFormulaSheetBinding
from interchange.document.models.DocumentModel import CadDocument

# a native fusion capture supplies the original parameter graph and opaque payload
KProductSource = (
    FilePath(__file__).parents[3]
    / "re/Fusion/Study/parameterexpressions-3ddbef2b20bd/product_sum.f3d"
)


# the public writer provides the source binding and archive exactly as users receive it
@Pytest.fixture
def StandaloneSheet(TmpPath: FilePath) -> tuple[CadDocument, FilePath]:
    Document = OpenDocument(KProductSource, strict=False)
    Export = TmpPath / "parameters.FCStd"
    _ = WriteDocument(Document, Export)
    return Document, Export


# native save retains the xml metadata and drops the extra zip manifest and carrier entry
@ContextManager
def SaveWorkbook(Export: FilePath, Saved: FilePath) -> Iterator[Element]:
    with ZipFile(Export) as Archive:
        RootValue = fromstring(Archive.read("Document.xml"))
    yield RootValue
    with ZipFile(Saved, "w") as Archive:
        Archive.writestr("Document.xml", tostring(RootValue, encoding="utf-8"))


# one altered driver must update the saved result across repeated import and export
def TestSavedSheet(StandaloneSheet: tuple[CadDocument, FilePath]) -> None:
    Original, Export = StandaloneSheet
    Saved = Export.with_name("saved.FCStd")
    Formula = Original.parameter("fusion-parameter-205").expression
    for EditText, ScaleText, DriverValue, ScaleValue, ResultValue in (
        ("=8 mm", "=2.5", 0.8, 2.5, 2.1),
        ("=-2 mm", "3.5", -0.2, 3.5, -0.6),
    ):
        with SaveWorkbook(Export, Saved) as RootValue:
            Cell = RootValue.find(".//Cell[@alias='fusion_parameter_202']")
            Scale = RootValue.find(".//Cell[@alias='fusion_parameter_203']")
            assert Cell is not None and Scale is not None
            Cell.set("content", EditText)
            Scale.set("content", ScaleText)
        Readback = OpenDocument(Saved)
        Driver = Readback.parameter("fusion-parameter-202")
        Scalar = Readback.parameter("fusion-parameter-203")
        Result = Readback.parameter("fusion-parameter-205")
        assert (Driver.value.value, Driver.value.unit) == (DriverValue, "cm")
        assert (Scalar.value.value, Scalar.value.unit) == (ScaleValue, "")
        assert (Result.value.value, Result.value.unit) == (ResultValue, "cm")
        assert Result.expression == Formula
        assert Readback.brep_payloads == Original.brep_payloads
        _ = WriteDocument(Readback, Export, overwrite=True)
        assert OpenDocument(Export) == Readback


# legacy snapshots keep their prior behavior even when a saved cell is different
def TestUnboundSheet(StandaloneSheet: tuple[CadDocument, FilePath]) -> None:
    Original, Export = StandaloneSheet
    Saved = Export.with_name("unbound.FCStd")
    with SaveWorkbook(Export, Saved) as RootValue:
        Props = RootValue.find("./ObjectData/Object[@name='KitMetadata']/Properties")
        assert Props is not None
        Binding = Props.find(f"./Property[@name='{KFormulaSheetBinding}']")
        assert Binding is not None
        Props.remove(Binding)
        Props.set("Count", str(int(Props.attrib["Count"]) - 1))
        Cell = RootValue.find(".//Cell[@alias='fusion_parameter_202']")
        assert Cell is not None
        Cell.set("content", "=8 mm")
    assert OpenDocument(Saved) == Original


# comparable native saves with unsupported edits must fail rather than return stale parameters
@Pytest.mark.parametrize("Change", ("formula", "unit", "extra cell", "moved alias"))
def TestConflictingSheet(
    StandaloneSheet: tuple[CadDocument, FilePath], Change: str
) -> None:
    _, Export = StandaloneSheet
    Saved = Export.with_name("conflict.FCStd")
    with SaveWorkbook(Export, Saved) as RootValue:
        Cells = RootValue.find(".//Property[@name='cells']/Cells")
        assert Cells is not None
        Driver = Cells.find("./Cell[@alias='fusion_parameter_202']")
        Result = Cells.find("./Cell[@alias='fusion_parameter_205']")
        assert Driver is not None and Result is not None
        if Change == "formula":
            Result.set("content", "=19.25 mm")
        elif Change == "unit":
            Driver.set("content", "=7.3 deg")
        elif Change == "extra cell":
            Cells.set("Count", str(int(Cells.attrib["Count"]) + 1))
            _ = SubElement(Cells, "Cell", {"address": "C1", "content": "=1"})
        else:
            Driver.set("address", "C1")
    with Pytest.raises(FreeCadAdapterA, match="spreadsheet"):
        OpenDocument(Saved)
