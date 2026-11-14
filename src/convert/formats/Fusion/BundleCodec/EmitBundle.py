from convert.formats.Fusion.AssetCodec.Zip.EmitAssetZip import EmitAssetZip
from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.formats.Fusion.BundleCodec.Json.EmitJson import EmitJson
from convert.formats.Fusion.BundleCodec.Json.EmitModel import EmitModel
from convert.formats.Fusion.BundleCodec.Json.ReadModel import ReadModel
from convert.formats.Fusion.BundleCodec.Model.FusionBundle import FusionBundle
from convert.formats.Fusion.BundleCodec.Validation.CheckModel import CheckModel


def EmitBundle(Value: FusionBundle) -> bytes:
    CheckModel(Value.Description)
    Manifest = EmitJson({"root": Value.Description.RootPath})
    Description = EmitJson(EmitModel(Value.Description))
    _ = ReadModel(Manifest, Description)
    Names = {Entry.MemberPath for Entry in Value.Description.Graph.Objects}
    if (
        len(Value.Documents) != len(Names)
        or {Entry.FileName for Entry in Value.Documents} != Names
    ):
        raise ValueError("Fusion bundle document payloads disagree with design graph")
    Members = tuple(
        ZipAssetRow(Entry.FileName, Entry.DataValue, False) for Entry in Value.Documents
    )
    return EmitAssetZip(
        Members
        + (
            ZipAssetRow("Manifest.json", Manifest, False),
            ZipAssetRow("DesignDescription.json", Description, False),
        )
    )
