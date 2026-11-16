from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)

# inflate ratio must remain consistent across callers so section boundaries and object references remain consistent
KInflateRatio = 64

# inflate floor must remain consistent across callers so section boundaries and object references remain consistent
KInflateFloor = 0x100000

# inflate ceiling must remain consistent across callers so section boundaries and object references remain consistent
KInflateCeiling = 0x40000000


# invalid budget input must fail here so section boundaries and object references remain consistent
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
