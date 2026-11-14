from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)

KInflateRatio = 64
KInflateFloor = 0x100000
KInflateCeiling = 0x40000000


def CheckBudget(Content: bytes, SectionInfos: tuple[DwgSectionInfo, ...]) -> None:
    Declared = sum(
        SectionInfo.PageCount * SectionInfo.MaxPageSize for SectionInfo in SectionInfos
    )
    Budget = min(len(Content) * KInflateRatio + KInflateFloor, KInflateCeiling)
    if Declared > Budget:
        raise ValueError(
            "DWG sections declare more inflated data than the expansion budget"
        )
    PageNumbers = [
        PageRef.PageNumber
        for SectionInfo in SectionInfos
        for PageRef in SectionInfo.PageRefs
    ]
    if len(set(PageNumbers)) != len(PageNumbers):
        raise ValueError("DWG data page is claimed by more than one section entry")
    NameTexts = [
        SectionInfo.SectionName
        for SectionInfo in SectionInfos
        if SectionInfo.SectionName
    ]
    if len(set(NameTexts)) != len(NameTexts):
        raise ValueError("DWG section names are duplicated")
