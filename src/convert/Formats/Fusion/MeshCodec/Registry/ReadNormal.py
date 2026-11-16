from convert.Formats.Fusion.MeshCodec.Wire.ProtoBytes import ProtoBytes
from convert.Formats.Fusion.MeshCodec.Wire.ProtoNumber import ProtoNumber
from convert.Formats.Fusion.MeshCodec.Wire.ProtoText import ProtoText
from convert.Formats.Fusion.MeshCodec.Wire.SelectFields import SelectFields


# the normal operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadNormal(Payload: bytes) -> tuple[str, str, str]:
    IdField, Declaration = SelectFields(Payload, (3, 5))
    Element, Values, Indices = SelectFields(ProtoBytes(Declaration), (1, 2, 3))
    if ProtoNumber(Element) != 5:
        raise ValueError("Unsupported Fusion mesh normal element")
    return ProtoText(IdField), ProtoText(Values), ProtoText(Indices)
