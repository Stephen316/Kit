from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderRecords import BuildRecords
from convert.Formats.Fusion.GeometryCodec.EmitSmbHeader import EmitSmbHeader
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.Formats.Fusion.GeometryCodec.EncodeSmbValue import EncodeSmbValue
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# the cylinder smb operation needs a consistent construction rule so geometric values retain their native record boundaries
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
