from convert.formats.Fusion.GeometryCodec.EmitSmbHeader import EmitSmbHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.formats.Fusion.GeometryCodec.Prism.CuboidRecords import CuboidRecords
from convert.formats.Fusion.GeometryCodec.Prism.EncodePrismVal import EncodePrismVal


def EmitCuboidSmb(Model: CuboidBody, Stamp: GeometryStamp) -> bytes:
    Parts = [EmitSmbHeader(Stamp)]
    for Record in CuboidRecords(Model):
        Parts.append(EncodeSmbName(Record.NameValue))
        Parts.extend(
            EncodePrismVal(Value, Record.NameValue, Index)
            for Index, Value in enumerate(Record.Fields)
        )
        Parts.append(b"\x11")
    Parts.append(EncodeSmbName("End-of-ASM-data"))
    return b"".join(Parts)
