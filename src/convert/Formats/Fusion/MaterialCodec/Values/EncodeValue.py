from struct import pack as PackValue

from convert.Formats.Fusion.MaterialCodec.Limits import KMaxCount, KMaxStream
from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import KMaterialValue
from convert.Formats.Fusion.MaterialCodec.Values.EncodeScalar import EncodeScalar
from convert.Formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


# the value operation needs a consistent construction rule so typed appearance properties retain their native identifiers
def EncodeValue(Value: KMaterialValue, Field: PropertySpec) -> bytes:
    if Field.ValueKind == "TextureURI":
        if (
            not isinstance(Value, tuple)
            or len(Value) > 255
            or not all(isinstance(Entry, str) for Entry in Value)
        ):
            raise ValueError("Fusion texture list must hold at most 255 texts")
        return bytes((len(Value),)) + b"".join(
            EncodeText(str(Entry)) for Entry in Value
        )
    if Field.IsMultiple:
        if not isinstance(Value, tuple) or len(Value) > KMaxCount:
            raise ValueError("Fusion material list exceeds the count limit")
        Payload = bytearray(PackValue("<I", len(Value)))
        for Entry in Value:
            Payload.extend(EncodeScalar(Entry, Field))
            if len(Payload) > KMaxStream:
                raise ValueError("Fusion material list exceeds the size limit")
        return bytes(Payload)
    if isinstance(Value, tuple):
        raise ValueError("Fusion material property does not allow multiple values")
    return EncodeScalar(Value, Field)
