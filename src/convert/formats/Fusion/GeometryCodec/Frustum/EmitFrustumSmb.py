from convert.formats.Fusion.GeometryCodec.EmitSmbHeader import EmitSmbHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.GeometryCodec.EncodeSmbValue import EncodeSmbValue
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumRecords import FrustumRecords
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def EmitFrustumSmb(Model: FrustumBody, Stamp: GeometryStamp) -> bytes:
    Parts = [EmitSmbHeader(Stamp)]
    for Record in FrustumRecords(Model):
        Parts.append(EncodeSmbName(Record.NameValue))
        Parts.extend(
            EncodeSmbValue(Value, Record.NameValue, Index)
            for Index, Value in enumerate(Record.Fields)
        )
        Parts.append(b"\x11")
    Parts.append(EncodeSmbName("End-of-ASM-data"))
    return b"".join(Parts)
