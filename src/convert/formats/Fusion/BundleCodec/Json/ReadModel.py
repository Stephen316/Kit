from convert.formats.Fusion.BundleCodec.Json.JsonScalar import JsonString
from convert.formats.Fusion.BundleCodec.Json.JsonShape import JsonArray, JsonObject
from convert.formats.Fusion.BundleCodec.Json.ReadGraph import ReadGraph
from convert.formats.Fusion.BundleCodec.Json.ReadJson import ReadJson
from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel


def ReadModel(Manifest: bytes, Description: bytes) -> BundleModel:
    RootValue = JsonObject(ReadJson(Manifest), "root")
    Envelope = JsonObject(ReadJson(Description), "name version designDescription")
    if (
        Envelope["name"] != "Autodesk Design Description"
        or Envelope["version"] != "0.1"
    ):
        raise ValueError("Unsupported Fusion bundle description version")
    Fields = JsonObject(
        Envelope["designDescription"], "id name currentVersion designGraphs"
    )
    Graphs = JsonArray(Fields["designGraphs"])
    if len(Graphs) != 1:
        raise ValueError("Fusion bundle requires one closed design graph")
    return BundleModel(
        JsonString(Fields["id"]),
        JsonString(Fields["name"]),
        JsonString(Fields["currentVersion"]),
        ReadGraph(Graphs[0]),
        JsonString(RootValue["root"]),
    )
