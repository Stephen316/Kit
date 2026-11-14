from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)

KMaxPageBytes = 0x400000


def CheckSection(SectionInfo: DwgSectionInfo) -> None:
    NameText = SectionInfo.SectionName
    if SectionInfo.CompressFlag not in (1, 2):
        raise ValueError(
            f"DWG section {NameText!r} compression flag {SectionInfo.CompressFlag} is unsupported"
        )
    if SectionInfo.EncryptFlag == 1:
        raise ValueError(f"DWG section {NameText!r} is encrypted")
    if SectionInfo.EncryptFlag not in (0, 2):
        raise ValueError(
            f"DWG section {NameText!r} encryption flag {SectionInfo.EncryptFlag} is unsupported"
        )
    if SectionInfo.PageCount > 0 and not 0 < SectionInfo.MaxPageSize <= KMaxPageBytes:
        raise ValueError(f"DWG section {NameText!r} page size is out of range")
    if SectionInfo.DataSize > SectionInfo.PageCount * SectionInfo.MaxPageSize:
        raise ValueError(
            f"DWG section {NameText!r} declares more data than its pages hold"
        )
