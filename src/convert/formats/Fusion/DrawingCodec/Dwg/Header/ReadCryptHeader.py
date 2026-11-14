from binascii import crc32 as CrcThirtyTwo

from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Header.MakeCryptMask import MakeCryptMask
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)

KCryptSize = 0x6C
KCryptMask = MakeCryptMask(KCryptSize)
KFileIdBytes = b"AcFssFcAJMB\x00"


def ReadCryptHeader(Content: bytes) -> DwgCryptHeader:
    Encoded = TakeSpan(Content, 0x80, KCryptSize, "encrypted R2004 header")
    Decoded = bytes(
        LeftByte ^ RightByte
        for LeftByte, RightByte in zip(Encoded, KCryptMask, strict=True)
    )
    if Decoded[:12] != KFileIdBytes:
        raise ValueError("DWG R2004 header file id string mismatch")
    Fields = ReadFields(Decoded, 12, "<3I3I2I2Q2I3IIQ4I", "R2004 header fields")
    if CrcThirtyTwo(Decoded[:0x68] + bytes(4)) != Fields[20]:
        raise ValueError("DWG R2004 header CRC mismatch")
    Mirror = Content[Fields[9] : Fields[9] + KCryptSize]
    return DwgCryptHeader(
        FileIdText=KFileIdBytes[:11].decode("ascii"),
        FixedWords=Fields[0:3],
        RootGap=Fields[3],
        LeftGap=Fields[4],
        RightGap=Fields[5],
        ReservedWord=Fields[6],
        LastPageId=Fields[7],
        LastPageEnd=Fields[8],
        SecondAddress=Fields[9],
        GapAmount=Fields[10],
        PageAmount=Fields[11],
        LayoutWords=Fields[12:15],
        PageMapId=Fields[15],
        PageMapAddress=Fields[16],
        SectionMapId=Fields[17],
        PageArraySize=Fields[18],
        GapArraySize=Fields[19],
        CrcValue=Fields[20],
        MirrorMatches=Mirror == Encoded,
    )
