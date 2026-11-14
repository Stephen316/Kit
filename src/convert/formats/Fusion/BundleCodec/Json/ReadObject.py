from convert.formats.Fusion.BundleCodec.Json.JsonScalar import JsonInteger, JsonString
from convert.formats.Fusion.BundleCodec.Json.JsonShape import JsonArray, JsonObject
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Json.ReadMetadata import ReadMetadata
from convert.formats.Fusion.BundleCodec.Json.ReadRefs import ReadRefs
from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject


def ReadObject(Value: KJsonValue) -> BundleObject:
    KeyNames = (
        "id version about lineage from relativePath downloadAs "
        + "friendlyName displayName zipped rootFile contentType shareInfo "
        + "references metadata"
    )
    HasCreated = isinstance(Value, dict) and "createdAt" in Value
    Fields = JsonObject(Value, KeyNames + " createdAt" if HasCreated else KeyNames)
    if (
        Fields["zipped"] is not False
        or Fields["rootFile"] != ""
        or Fields["shareInfo"] is not None
    ):
        raise ValueError("Unsupported Fusion bundle object packaging")
    ContentType = JsonString(Fields["contentType"])
    if ContentType != "f3d" and ContentType != "f2d":
        raise ValueError("Unsupported Fusion bundle document type")
    return BundleObject(
        JsonInteger(Fields["id"]),
        JsonInteger(Fields["version"]),
        JsonString(Fields["about"]),
        JsonString(Fields["lineage"]),
        JsonString(Fields["from"]),
        JsonString(Fields["relativePath"]),
        JsonString(Fields["downloadAs"]),
        JsonString(Fields["friendlyName"]),
        JsonString(Fields["displayName"]),
        "f3d" if ContentType == "f3d" else "f2d",
        tuple(ReadRefs(Entry) for Entry in JsonArray(Fields["references"])),
        ReadMetadata(Fields["metadata"]),
        JsonString(Fields["createdAt"]) if HasCreated else None,
    )
