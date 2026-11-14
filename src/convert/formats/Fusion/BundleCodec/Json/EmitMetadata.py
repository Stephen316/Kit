from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Model.BundleText import BundleText


def EmitMetadata(Values: tuple[BundleText, ...]) -> dict[str, KJsonValue]:
    if len(Values) > 4094 or len({Value.FieldName for Value in Values}) != len(Values):
        raise ValueError("Duplicate or oversized Fusion bundle metadata")
    return {Value.FieldName: Value.TextValue for Value in Values}
