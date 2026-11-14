from convert.formats.Fusion.BundleCodec.Json.EmitMetadata import EmitMetadata
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs


def EmitRefs(Value: BundleRefs) -> KJsonValue:
    return {
        "type": Value.KindValue,
        "ids": list(Value.Targets),
        "relationships": [
            {"id": Entry.TargetId, "metadata": EmitMetadata(Entry.Metadata)}
            for Entry in Value.Relations
        ],
    }
