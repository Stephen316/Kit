from binascii import crc32 as CrcThirtyTwo
from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Header.ReadCryptHeader import (
    KCryptMask,
    KFileIdBytes,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader

KHeaderTrail = bytes.fromhex("f8466a0496730ed9162f6768d4f74a4ad0576876")


def EmitFileHead(FileHeader: DwgFileHeader) -> bytes:
    Output = FileHeader.VersionText.encode("latin-1") + FileHeader.PaddingBytes
    Output += PackFields(
        "<BBIBBH",
        FileHeader.MaintenanceVersion,
        FileHeader.HeaderMarker,
        FileHeader.PreviewAddress,
        FileHeader.AppVersion,
        FileHeader.AppMaintenance,
        FileHeader.CodePage,
    )
    Output += FileHeader.ReservedTriple
    Output += PackFields(
        "<7I",
        FileHeader.SecurityFlags,
        FileHeader.ReservedAddress,
        FileHeader.SummaryAddress,
        FileHeader.VbaAddress,
        FileHeader.CryptAddress,
        FileHeader.AppInfoAddress,
        FileHeader.AppHistoryAddress,
    )
    Output += PackFields("<19I", *FileHeader.TrailingWords)
    if len(Output) != 0x80:
        raise ValueError("DWG file header fields do not fill 128 bytes")
    return Output


def EmitCrypt(CryptHeader: DwgCryptHeader) -> bytes:
    Plain = KFileIdBytes + PackFields(
        "<3I3I2I2Q2I3IIQ3I",
        *CryptHeader.FixedWords,
        CryptHeader.RootGap,
        CryptHeader.LeftGap,
        CryptHeader.RightGap,
        CryptHeader.ReservedWord,
        CryptHeader.LastPageId,
        CryptHeader.LastPageEnd,
        CryptHeader.SecondAddress,
        CryptHeader.GapAmount,
        CryptHeader.PageAmount,
        *CryptHeader.LayoutWords,
        CryptHeader.PageMapId,
        CryptHeader.PageMapAddress,
        CryptHeader.SectionMapId,
        CryptHeader.PageArraySize,
        CryptHeader.GapArraySize,
    )
    Plain += PackFields("<I", CrcThirtyTwo(Plain + bytes(4)))
    return bytes(
        LeftByte ^ RightByte
        for LeftByte, RightByte in zip(Plain, KCryptMask, strict=True)
    )
