from pathlib import Path as FilePath
from xml.etree.ElementTree import fromstring as ParseXml, tostring as XmlBytes
from zipfile import ZipFile

import pytest as Pytest

from convert import write_document as WriteDocument
from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.EditScale.ScaleBinding import KScaleBinding
from interchange.enums.EnumDocument import Capability
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath
from tests.convert.api.ScaleCases import KScaleCases

# every reconstructed source has a live scale graph with its original body count
KScaleFiles = tuple((Value[0], Value[-1]) for Value in KScaleCases)


# native shape entries must appear in restore order even when names sort differently
@KRequiresCodec
@Pytest.mark.parametrize("Sample,Count", KScaleFiles)
def TestScaleWrite(Sample: str, Count: int, TmpPath: FilePath) -> None:
    Document = OpenDocument(KStudyPath / Sample, StrictMode=False)
    Output = TmpPath / "scale.FCStd"
    Result = WriteDocument(Document, Output, destination_format="freecad.fcstd")
    assert Result.vendor_loadable and Result.application_usable
    assert Capability.PARAMETRIC_HISTORY in Result.native_capabilities
    assert Capability.PARAMETRIC_HISTORY not in Result.carrier_capabilities
    with ZipFile(Output) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
        Declared = RootValue.findall("./Objects/Object")
        assert (
            sum(Value.get("type") == "Part::Extrusion" for Value in Declared) == Count
        )
        assert sum(Value.get("type") == "Part::Scale" for Value in Declared) == Count
        Shapes = tuple(
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".Shape.brp")
        )
        Restore = tuple(
            FileName
            for Value in RootValue.findall(
                "./ObjectData/Object/Properties/Property[@name='Shape']/Part"
            )
            if (FileName := Value.get("file"))
        )
        assert Shapes == Restore and len(Shapes) == Count * 2
        Binding = RootValue.find(
            f"./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='{KScaleBinding}']/String"
        )
        assert Binding is not None
        assert Binding.get("value") == Document.feature_timeline[-1].id
    assert OpenDocument(Output, StrictMode=False) == Document


# modified native controls must never fall back to the unmodified interchange snapshot
@KRequiresCodec
def TestScaleGate(TmpPath: FilePath) -> None:
    Document = OpenDocument(KStudyPath / KScaleFiles[1][0], StrictMode=False)
    Output, Modified = TmpPath / "scale.FCStd", TmpPath / "changed.FCStd"
    _ = WriteDocument(Document, Output, destination_format="freecad.fcstd")
    with ZipFile(Output) as Original, ZipFile(Modified, "w") as Archive:
        RootValue = ParseXml(Original.read("Document.xml"))
        (Value,) = RootValue.findall(
            "./ObjectData/Object/Properties/Property[@name='UniformScale']/Float"
        )
        assert float(Value.get("value", "nan")) == 1.75
        Value.set("value", "0.65")
        for ItemValue in Original.infolist():
            Archive.writestr(
                ItemValue,
                (
                    XmlBytes(RootValue)
                    if ItemValue.filename == "Document.xml"
                    else Original.read(ItemValue)
                ),
            )
    with Pytest.raises(FreeCadAdapterA, match=r"FreeCAD editable Scale .*UniformScale"):
        _ = OpenDocument(Modified, StrictMode=False)
