from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import KMaterialValue
from convert.Formats.Fusion.MaterialCodec.Values.DecodeScalar import DecodeScalar
from convert.Formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


# the value operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def DecodeValue(ReaderMut: MaterialReader, Field: PropertySpec) -> KMaterialValue:
    if Field.ValueKind == "TextureURI":
        return tuple(ReaderMut.ReadText() for _ in range(ReaderMut.ReadSmall()))
    if Field.IsMultiple:
        return tuple(
            DecodeScalar(ReaderMut, Field) for _ in range(ReaderMut.ReadCount())
        )
    return DecodeScalar(ReaderMut, Field)
