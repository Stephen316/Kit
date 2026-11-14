from convert.formats.Fusion.BundleCodec.Json.EmitMetadata import EmitMetadata
from convert.formats.Fusion.BundleCodec.Json.EmitRefs import EmitRefs
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject


def EmitObject(Value: BundleObject) -> KJsonValue:
    Fields: dict[str, KJsonValue] = {
        "id": Value.ObjectId,
        "version": Value.Version,
        "about": Value.VersionUrn,
        "lineage": Value.LineageUrn,
        "from": Value.StorageUrn,
        "relativePath": Value.MemberPath,
        "downloadAs": Value.DownloadAs,
        "friendlyName": Value.FriendlyName,
        "displayName": Value.DisplayName,
        "zipped": False,
        "rootFile": "",
        "contentType": Value.ContentType,
        "shareInfo": None,
        "references": [EmitRefs(Entry) for Entry in Value.References],
        "metadata": EmitMetadata(Value.Metadata),
    }
    if Value.CreatedAt is not None:
        Fields["createdAt"] = Value.CreatedAt
    return Fields
