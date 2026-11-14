from convert.formats.Fusion.MeshCodec.Wire.ProtoBytes import ProtoBytes
from convert.formats.Fusion.MeshCodec.Wire.ProtoNumber import ProtoNumber
from convert.formats.Fusion.MeshCodec.Wire.ProtoText import ProtoText
from convert.formats.Fusion.MeshCodec.Wire.SelectFields import SelectFields


def ReadNormal(Payload: bytes) -> tuple[str, str, str]:
    IdField, Declaration = SelectFields(Payload, (3, 5))
    Element, Values, Indices = SelectFields(ProtoBytes(Declaration), (1, 2, 3))
    if ProtoNumber(Element) != 5:
        raise ValueError("Unsupported Fusion mesh normal element")
    return ProtoText(IdField), ProtoText(Values), ProtoText(Indices)
