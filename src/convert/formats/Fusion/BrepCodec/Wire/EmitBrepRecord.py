from convert.formats.Fusion.BrepCodec.Wire.EncodeBrepValue import EncodeBrepValue
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the boundary representation record operation needs a consistent construction rule so topology identity survives native history reconstruction
def EmitBrepRecord(Record: GeometryRecord) -> bytes:
    Fields = b"".join(
        EncodeBrepValue(Value, Record.NameValue, Index)
        for Index, Value in enumerate(Record.Fields)
    )
    return EncodeSmbName(Record.NameValue) + Fields + b"\x11"
