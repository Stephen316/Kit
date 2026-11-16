from convert.Formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.Formats.Fusion.BundleCodec.Model.BundleText import BundleText


# the metadata operation needs a consistent construction rule so linked archive members retain their document relationships
def EmitMetadata(Values: tuple[BundleText, ...]) -> dict[str, KJsonValue]:
    if len(Values) > 4094 or len({Value.FieldName for Value in Values}) != len(Values):
        raise ValueError("Duplicate or oversized Fusion bundle metadata")
    return {Value.FieldName: Value.TextValue for Value in Values}
