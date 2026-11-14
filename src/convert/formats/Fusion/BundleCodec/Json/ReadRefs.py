from convert.formats.Fusion.BundleCodec.Json.JsonScalar import JsonInteger, JsonString
from convert.formats.Fusion.BundleCodec.Json.JsonShape import JsonArray, JsonObject
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Json.ReadMetadata import ReadMetadata
from convert.formats.Fusion.BundleCodec.Model.BundleLink import BundleLink
from convert.formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs


def ReadLink(Value: KJsonValue) -> BundleLink:
    Fields = JsonObject(Value, "id metadata")
    return BundleLink(JsonInteger(Fields["id"]), ReadMetadata(Fields["metadata"]))


def ReadRefs(Value: KJsonValue) -> BundleRefs:
    Fields = JsonObject(Value, "type ids relationships")
    KindValue = JsonString(Fields["type"])
    if KindValue != "XREF" and KindValue != "DERIVED":
        raise ValueError("Unsupported Fusion bundle reference type")
    return BundleRefs(
        "XREF" if KindValue == "XREF" else "DERIVED",
        tuple(JsonInteger(Target) for Target in JsonArray(Fields["ids"])),
        tuple(ReadLink(Target) for Target in JsonArray(Fields["relationships"])),
    )
