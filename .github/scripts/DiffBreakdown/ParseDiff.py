from __future__ import annotations


def DecodePath(PathData: bytes) -> str:
    return PathData.decode("utf-8", "surrogateescape")


def ParseNumstat(RawData: bytes) -> list[tuple[str, str | None, int, int, bool]]:
    EntryList: list[tuple[str, str | None, int, int, bool]] = []
    Records = iter(RawData.split(b"\0"))
    for Record in Records:
        if not Record:
            continue
        AddText, DelText, PathData = Record.split(b"\t", 2)
        OldPath = None
        if not PathData:
            OldPath = DecodePath(next(Records))
            PathData = next(Records)
        IsBinary = AddText == b"-" or DelText == b"-"
        AddCount = 0 if IsBinary else int(AddText)
        DelCount = 0 if IsBinary else int(DelText)
        EntryList.append((DecodePath(PathData), OldPath, AddCount, DelCount, IsBinary))
    return EntryList


def ParseStatuses(RawData: bytes) -> dict[str, str]:
    StatusMap: dict[str, str] = {}
    Fields = iter(RawData.split(b"\0"))
    for StatusData in Fields:
        if not StatusData:
            continue
        PathText = DecodePath(next(Fields))
        if StatusData[:1] in (b"R", b"C"):
            PathText = DecodePath(next(Fields))
        StatusMap[PathText] = StatusData.decode()
    return StatusMap
