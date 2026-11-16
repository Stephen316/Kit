from pathlib import Path as FilePath
from zipfile import ZIP_DEFLATED as KZipDeflated
from zipfile import ZipFile

from convert.Formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from convert.Formats.Fusion.MaterialCodec.EncodeMaterials import EncodeMaterials
from convert.Formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from tests.Convert.Formats.FusionCodec.Materials.ChangeAssets import ChangeAssets
from tests.Convert.Formats.FusionCodec.Materials.CheckStore import CheckStore
from tests.Convert.Formats.FusionCodec.Materials.ReadNative import ReadNative


# the archive edit contract needs boundary coverage so stored document relationships remain consistent
def TestArchiveEdit(TmpPath: FilePath) -> None:
    Native = ReadNative()
    Changed = ChangeAssets(DecodeMaterials(Native.Streams, Native.Schemas))
    Encoded = EncodeMaterials(Changed, Native.Schemas)
    Target = TmpPath / "materials.zip"
    Members = {
        "AssetTableOfContents.bin": Encoded.TableData,
        "DefinitionIteratorProperties.bin": Encoded.DefinitionData,
        "InstanceProperties.bin": Encoded.InstanceData,
    }
    with ZipFile(Target, "w", compression=KZipDeflated) as Archive:
        for NameValue, Payload in Members.items():
            Archive.writestr("AssetData/" + NameValue, Payload)
    with ZipFile(Target) as Archive:
        Restored = MaterialData(
            *(Archive.read("AssetData/" + NameValue) for NameValue in Members)
        )
    assert DecodeMaterials(Restored, Native.Schemas) == Changed
    CheckStore(Restored.InstanceData)
    CheckStore(Restored.DefinitionData)
