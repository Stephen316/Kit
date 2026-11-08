# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
import xml.etree.ElementTree as XmlTree
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.base.TransferContract import TransferMode
from interchange.enums.EnumDocument import Capability

# authored fusion controls exercise normal source and target entry points together
KFormulaStudy = FilePath(__file__).parents[3] / "re" / "Fusion" / "Study"


# native cells must retain every repeated and grouped operand through exact aliases
@Pytest.mark.parametrize(
    ("SampleName", "FormulaText"),
    (
        ("product_sum", "fusion_parameter_202 * fusion_parameter_203 + 1 mm"),
        (
            "parenthesized",
            "( fusion_parameter_202 + fusion_parameter_204 ) / fusion_parameter_203",
        ),
        (
            "repeated_reference",
            "fusion_parameter_202 + fusion_parameter_202 + fusion_parameter_204",
        ),
        ("unary_reference", "- fusion_parameter_202 + 20 mm"),
    ),
)
def TestFusionSheet(TmpPath: FilePath, SampleName: str, FormulaText: str) -> None:
    Source = KFormulaStudy / "parameterexpressions-3ddbef2b20bd" / f"{SampleName}.f3d"
    Document = OpenDocument(Source, strict=False)
    Target = TmpPath / "parameters.FCStd"
    Result = WriteDocument(Document, Target)
    Modes = {Value.capability: Value.mode for Value in Result.transfers}
    assert Modes[Capability.EXPRESSIONS] is TransferMode.NATIVE
    with ZipFile(Target) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Cell = RootValue.find(".//Cell[@alias='fusion_parameter_205']")
        Scale = RootValue.find(".//Cell[@alias='fusion_parameter_203']")
        assert Cell is not None and Cell.get("content") == "=" + FormulaText
        assert Scale is not None and Scale.get("content") == "=2.5"
    assert OpenDocument(Target).parameters == Document.parameters


# an unsupported formula must keep its original definition without claiming native execution
def TestFormulaGap(TmpPath: FilePath) -> None:
    Source = (
        KFormulaStudy
        / "parameterexpressions-3ddbef2b20bd"
        / "function_outside_subset.f3d"
    )
    Document = OpenDocument(Source, strict=False)
    Target = TmpPath / "parameters.FCStd"
    Result = WriteDocument(Document, Target)
    Modes = {Value.capability: Value.mode for Value in Result.transfers}
    assert Modes[Capability.EXPRESSIONS] is TransferMode.MIXED
    with ZipFile(Target) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Cell = RootValue.find(".//Cell[@alias='fusion_parameter_205']")
        assert Cell is not None and "sqrt" not in Cell.get("content", "")
    assert OpenDocument(Target).parameters == Document.parameters
