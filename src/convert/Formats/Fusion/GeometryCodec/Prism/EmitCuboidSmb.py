from convert.Formats.Fusion.GeometryCodec.EmitSmbHeader import EmitSmbHeader
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidRecords import CuboidRecords
from convert.Formats.Fusion.GeometryCodec.Prism.EncodePrismVal import EncodePrismVal


# the cuboid smb operation needs a consistent construction rule so geometric values retain their native record boundaries
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
