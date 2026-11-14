from convert.formats.Fusion.BundleCodec.Json.JsonScalar import JsonInteger, JsonString
from convert.formats.Fusion.BundleCodec.Json.JsonShape import JsonArray, JsonObject
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Json.ReadObject import ReadObject
from convert.formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph


def ReadGraph(Value: KJsonValue) -> BundleGraph:
    Fields = JsonObject(
        Value, "creationDate creatingService rootIds designObjectRefs designObjects"
    )
    if JsonArray(Fields["designObjectRefs"]):
        raise ValueError("External Fusion bundle object references are unsupported")
    return BundleGraph(
        JsonString(Fields["creationDate"]),
        JsonString(Fields["creatingService"]),
        tuple(JsonInteger(Entry) for Entry in JsonArray(Fields["rootIds"])),
        tuple(ReadObject(Entry) for Entry in JsonArray(Fields["designObjects"])),
    )
