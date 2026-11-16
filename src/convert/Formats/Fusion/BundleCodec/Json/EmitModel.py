from convert.Formats.Fusion.BundleCodec.Json.EmitObject import EmitObject
from convert.Formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.Formats.Fusion.BundleCodec.Model.BundleModel import BundleModel


# the model operation needs a consistent construction rule so linked archive members retain their document relationships
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
