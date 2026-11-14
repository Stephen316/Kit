from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderRecords import BuildRecords
from convert.formats.Fusion.GeometryCodec.EmitSmbHeader import EmitSmbHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.GeometryCodec.EncodeSmbValue import EncodeSmbValue
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def EmitCylinderSmb(Model: CylinderBody, Stamp: GeometryStamp) -> bytes:
    Parts = [EmitSmbHeader(Stamp)]
    for Record in BuildRecords(Model):
        Parts.append(EncodeSmbName(Record.NameValue))
        Parts.extend(
            EncodeSmbValue(Value, Record.NameValue, Index)
            for Index, Value in enumerate(Record.Fields)
        )
        Parts.append(b"\x11")
    Parts.append(EncodeSmbName("End-of-ASM-data"))
    return b"".join(Parts)
