from struct import pack as PackValue

from convert.Formats.Fusion.BrepCodec.Wire.EncodeBrepValue import EncodeBrepValue
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the prism val operation needs a consistent construction rule so profile topology remains connected to its extrusion history
def EncodePrismVal(Value: KGeometryValue, NameValue: str, Index: int) -> bytes:
    if isinstance(Value, tuple):
        Position = (NameValue, Index) in (
            ("straight-curve", 3),
            ("plane-surface", 3),
            ("point", 3),
        )
        return bytes((19 if Position else 20,)) + PackValue("<3d", *Value)
    return EncodeBrepValue(Value, NameValue, Index)


# the prism rows operation needs a consistent construction rule so profile topology remains connected to its extrusion history
def EmitPrismRows(Records: tuple[GeometryRecord, ...]) -> bytes:
    return b"".join(
        EncodeSmbName(Record.NameValue)
        + b"".join(
            EncodePrismVal(Value, Record.NameValue, Index)
            for Index, Value in enumerate(Record.Fields)
        )
        + b"\x11"
        for Record in Records
    )
