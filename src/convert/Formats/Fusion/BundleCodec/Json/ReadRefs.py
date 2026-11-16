from convert.Formats.Fusion.BundleCodec.Json.JsonScalar import JsonInteger, JsonString
from convert.Formats.Fusion.BundleCodec.Json.JsonShape import JsonArray, JsonObject
from convert.Formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.Formats.Fusion.BundleCodec.Json.ReadMetadata import ReadMetadata
from convert.Formats.Fusion.BundleCodec.Model.BundleLink import BundleLink
from convert.Formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs


# the link operation needs a distinct decoding boundary so linked archive members retain their document relationships
def ReadLink(Value: KJsonValue) -> BundleLink:
    Fields = JsonObject(Value, "id metadata")
    return BundleLink(JsonInteger(Fields["id"]), ReadMetadata(Fields["metadata"]))


# the references operation needs a distinct decoding boundary so linked archive members retain their document relationships
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
