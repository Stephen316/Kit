from io import BytesIO as ByteStream
from pathlib import Path as FilePath
from xml.etree.ElementTree import fromstring as ParseXml
from zipfile import ZipFile

from convert.formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from tests.convert.formats.FusionCodec.Materials.NativeMaterial import NativeMaterial
from tests.convert.formats.FusionCodec.Materials.ReadSchema import ReadSchema

KFeatureRoot = (
    FilePath(__file__).resolve().parents[5] / "re/Fusion/LocalOracle/Features"
)


def ReadNative() -> NativeMaterial:
    with ZipFile(KFeatureRoot / "extrude_07mm.f3d") as Archive:
        Member = next(
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".protein")
        )
        Protein = Archive.read(Member)
    with ZipFile(ByteStream(Protein)) as Archive:
        Prefix = next(
            NameValue.rsplit("/", 1)[0]
            for NameValue in Archive.namelist()
            if NameValue.endswith("AssetTableOfContents.bin")
        )
        Streams = MaterialData(
            *(
                Archive.read(Prefix + "/" + NameValue)
                for NameValue in (
                    "AssetTableOfContents.bin",
                    "DefinitionIteratorProperties.bin",
                    "InstanceProperties.bin",
                )
            )
        )
        Trees = tuple(
            ParseXml(Archive.read(NameValue))
            for NameValue in Archive.namelist()
            if "/Schemas/" in NameValue and NameValue.endswith(".xml")
        )
    Schemas = tuple(
        ReadSchema(XmlTree) for XmlTree in Trees if XmlTree.tag == "AssetSchema"
    )
    return NativeMaterial(Streams, Schemas)
