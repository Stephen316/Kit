from convert.formats.Fusion.BundleCodec.Json.EmitObject import EmitObject
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel


def EmitModel(Value: BundleModel) -> KJsonValue:
    GraphValue: KJsonValue = {
        "creationDate": Value.Graph.CreatedAt,
        "creatingService": Value.Graph.ServiceName,
        "rootIds": list(Value.Graph.RootIds),
        "designObjectRefs": [],
        "designObjects": [EmitObject(Entry) for Entry in Value.Graph.Objects],
    }
    return {
        "name": "Autodesk Design Description",
        "version": "0.1",
        "designDescription": {
            "id": Value.DesignId,
            "name": Value.DesignName,
            "currentVersion": Value.CurrentVersion,
            "designGraphs": [GraphValue],
        },
    }
