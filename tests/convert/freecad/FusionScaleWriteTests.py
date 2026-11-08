# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from xml.etree.ElementTree import fromstring as ParseXml, tostring as XmlBytes
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.EditScale.ScaleBinding import KScaleBinding
from interchange.enums.EnumDocument import Capability
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath
from tests.convert.api.ApiFusionScaleTests import KScaleCases

# every reconstructed source has a live scale graph with its original body count
KScaleFiles = tuple((Value[0], Value[-1]) for Value in KScaleCases)


# native shape entries must appear in restore order even when names sort differently
@KRequiresCodec
@Pytest.mark.parametrize("Sample,Count", KScaleFiles)
def TestScaleWrite(Sample: str, Count: int, TmpPath: FilePath) -> None:
    Document = OpenDocument(KStudyPath / Sample, strict=False)
    Output = TmpPath / "scale.FCStd"
    Result = WriteDocument(Document, Output, destination_format="freecad.fcstd")
    assert Result.vendor_loadable and Result.application_usable
    assert Capability.PARAMETRIC_HISTORY in Result.native_capabilities
    assert Capability.PARAMETRIC_HISTORY not in Result.carrier_capabilities
    with ZipFile(Output) as Archive:
        Root = ParseXml(Archive.read("Document.xml"))
        Declared = Root.findall("./Objects/Object")
        assert (
            sum(Value.get("type") == "Part::Extrusion" for Value in Declared) == Count
        )
        assert sum(Value.get("type") == "Part::Scale" for Value in Declared) == Count
        Shapes = tuple(
            Name for Name in Archive.namelist() if Name.endswith(".Shape.brp")
        )
        Restore = tuple(
            FileName
            for Value in Root.findall(
                "./ObjectData/Object/Properties/Property[@name='Shape']/Part"
            )
            if (FileName := Value.get("file"))
        )
        assert Shapes == Restore and len(Shapes) == Count * 2
        assert (
            Root.find(
                f"./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='{KScaleBinding}']/String"
            ).get("value")
            == Document.feature_timeline[-1].id
        )
    assert OpenDocument(Output, strict=False) == Document


# modified native controls must never fall back to the unmodified interchange snapshot
@KRequiresCodec
def TestScaleEditGate(TmpPath: FilePath) -> None:
    Document = OpenDocument(KStudyPath / KScaleFiles[1][0], strict=False)
    Output, Modified = TmpPath / "scale.FCStd", TmpPath / "changed.FCStd"
    WriteDocument(Document, Output, destination_format="freecad.fcstd")
    with ZipFile(Output) as Original, ZipFile(Modified, "w") as Archive:
        Root = ParseXml(Original.read("Document.xml"))
        (Value,) = Root.findall(
            "./ObjectData/Object/Properties/Property[@name='UniformScale']/Float"
        )
        assert float(Value.get("value", "nan")) == 1.75
        Value.set("value", "0.65")
        for Item in Original.infolist():
            Archive.writestr(
                Item,
                (
                    XmlBytes(Root)
                    if Item.filename == "Document.xml"
                    else Original.read(Item)
                ),
            )
    with Pytest.raises(FreeCadAdapterA, match="requires saved edit reconciliation"):
        OpenDocument(Modified, strict=False)
