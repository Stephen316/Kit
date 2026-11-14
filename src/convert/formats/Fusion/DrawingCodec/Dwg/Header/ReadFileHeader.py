from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader

KVersionTexts = frozenset({"AC1027", "AC1032"})


def ReadFileHeader(Content: bytes) -> DwgFileHeader:
    Prefix = TakeSpan(Content, 0, 0x80, "file header")
    VersionText = Prefix[:6].decode("latin-1")
    if VersionText not in KVersionTexts:
        raise ValueError(f"DWG version {VersionText!r} is unsupported")
    Release = ReadFields(Prefix, 0x0B, "<BBIBBH", "file header release fields")
    Words = ReadFields(Prefix, 0x18, "<26I", "file header address words")
    if Words[0] != 0:
        raise ValueError(f"DWG security flags {Words[0]:#x} are unsupported")
    if Words[4] != 0x80:
        raise ValueError(f"DWG R2004 header address {Words[4]:#x} is not 0x80")
    return DwgFileHeader(
        VersionText=VersionText,
        PaddingBytes=Prefix[6:11],
        MaintenanceVersion=Release[0],
        HeaderMarker=Release[1],
        PreviewAddress=Release[2],
        AppVersion=Release[3],
        AppMaintenance=Release[4],
        CodePage=Release[5],
        ReservedTriple=Prefix[0x15:0x18],
        SecurityFlags=Words[0],
        ReservedAddress=Words[1],
        SummaryAddress=Words[2],
        VbaAddress=Words[3],
        CryptAddress=Words[4],
        AppInfoAddress=Words[5],
        AppHistoryAddress=Words[6],
        TrailingWords=Words[7:],
    )
