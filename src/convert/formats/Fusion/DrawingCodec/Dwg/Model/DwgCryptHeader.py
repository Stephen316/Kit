from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgCryptHeader:
    FileIdText: str
    FixedWords: tuple[int, ...]
    RootGap: int
    LeftGap: int
    RightGap: int
    ReservedWord: int
    LastPageId: int
    LastPageEnd: int
    SecondAddress: int
    GapAmount: int
    PageAmount: int
    LayoutWords: tuple[int, ...]
    PageMapId: int
    PageMapAddress: int
    SectionMapId: int
    PageArraySize: int
    GapArraySize: int
    CrcValue: int
    MirrorMatches: bool
