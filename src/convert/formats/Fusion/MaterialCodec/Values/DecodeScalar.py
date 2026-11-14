from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import KScalarValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


def DecodeScalar(ReaderMut: MaterialReader, Field: PropertySpec) -> KScalarValue:
    if Field.ValueKind in ("String", "URL", "Uuid"):
        return ReaderMut.ReadText()
    if Field.ValueKind in ("Integer", "Choice"):
        return ReaderMut.ReadInt()
    if Field.ValueKind == "Boolean":
        return ReaderMut.ReadBool()
    if Field.ValueKind == "Float":
        if Field.UnitName is not None:
            return UnitValue(ReaderMut.ReadInt(), ReaderMut.ReadFloat())
        return ReaderMut.ReadFloat()
    if Field.ValueKind == "Color":
        return ColorValue(*(ReaderMut.ReadFloat() for _ in range(4)))
    if Field.ValueKind == "Reference":
        return None
    raise ValueError("Unsupported Fusion material property type")
