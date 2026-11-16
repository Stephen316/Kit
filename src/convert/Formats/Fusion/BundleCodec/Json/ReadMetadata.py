from convert.Formats.Fusion.BundleCodec.Json.JsonScalar import JsonString
from convert.Formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.Formats.Fusion.BundleCodec.Model.BundleText import BundleText


# the metadata operation needs a distinct decoding boundary so linked archive members retain their document relationships
def ReadMetadata(Value: KJsonValue) -> tuple[BundleText, ...]:
    if not isinstance(Value, dict) or len(Value) > 4094:
        raise ValueError("Invalid Fusion bundle metadata dictionary")
    return tuple(
        BundleText(JsonString(FieldName), JsonString(TextValue))
        for FieldName, TextValue in Value.items()
    )
