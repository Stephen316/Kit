from uuid import UUID

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.ShellDefaults import (
    KProductKey,
    KProductText,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import MakeFrame
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgAppEntry import DwgAppEntry
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgDayTime import DwgDayTime
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSummary import DwgSummary

# the free marks order must stay explicit so drawing objects retain valid ownership and reference relationships
KFreeMarks = (50, 100, 512, 0xFFFFFFFF)

# short count needs one explicit bound so native drawing authoring cannot accept inconsistent resource or layout limits
KShortCount = 4

# short fill must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KShortFill = 0x5555

# aux marker must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KAuxMarker = bytes.fromhex("ff8801")

# the aux version order must stay explicit so drawing objects retain valid ownership and reference relationships
KAuxVersion = (33, 285)

# the aux saved order must stay explicit so drawing objects retain valid ownership and reference relationships
KAuxSaved = (22, 46)

# the aux codes order must stay explicit so drawing objects retain valid ownership and reference relationships
KAuxCodes = (4, 1381, 0, 0, 0, 1, 0, 0, 0, 16843008, 65538)

# aux names must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KAuxNames = tuple(f"Code{Letter}" for Letter in "ABCDEF") + tuple(
    f"Reserved{Letter}" for Letter in "BCDEF"
)


# the record operation needs a consistent construction rule so drawing objects retain valid ownership and reference relationships
def MakeRecord(*Pairs: tuple[str, KDwgValue]) -> DwgRecord:
    return DwgRecord(tuple(DwgField(Called, Value) for Called, Value in Pairs))


# the author summary contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def AuthorSummary(Moment: DwgDayTime) -> DwgSummary:
    return DwgSummary(
        "", "", "", "", "", "", "", "", DwgDayTime(0, 0), Moment, Moment, (), (0, 0)
    )


# the author app info contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def AuthorAppInfo() -> DwgAppInfo:
    return DwgAppInfo(3, "AppInfoDataList", (DwgAppEntry(KProductKey, KProductText),))


# the free space contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def FreeSpace(ObjectCount: int, Moment: DwgDayTime) -> DwgRecord:
    Pairs = tuple(
        DwgRecord((DwgField("PairFirst", Marker), DwgField("PairSecond", 0)))
        for Marker in KFreeMarks
    )
    return DwgRecord(
        (
            DwgField("ReservedLong", 0),
            DwgField("ApproxObjects", ObjectCount),
            DwgField("TdUpdateDay", Moment.DayNumber),
            DwgField("TdUpdateMsec", Moment.MilliSeconds),
            DwgField("PairCount", len(Pairs)),
            DwgField("Pairs", Pairs),
        )
    )


# the aux header contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def AuxHeader(HandSeed: int, Moment: DwgDayTime) -> DwgRecord:
    Codes = tuple(zip(KAuxNames, KAuxCodes))
    return MakeRecord(
        ("AuxMarker", KAuxMarker),
        ("DwgVersion", KAuxVersion[0]),
        ("MaintVersion", KAuxVersion[1]),
        ("SaveCount", 1),
        ("MinusOne", 0xFFFFFFFF),
        ("SavesPartOne", 1),
        ("SavesPartTwo", 0),
        ("ReservedA", 0),
        ("SavedVersionA", KAuxSaved[0]),
        ("SavedMaintA", KAuxSaved[1]),
        ("SavedVersionB", KAuxSaved[0]),
        ("SavedMaintB", KAuxSaved[1]),
        *Codes,
        ("TdCreateDay", Moment.DayNumber),
        ("TdCreateMsec", Moment.MilliSeconds),
        ("TdUpdateDay", Moment.DayNumber),
        ("TdUpdateMsec", Moment.MilliSeconds),
        ("HandSeed", HandSeed),
        *((Called, 0) for Called in ("EduPlotStamp", "ReservedShort", "SavesDelta")),
        *((f"Reserved{Letter}", 0) for Letter in "GHI"),
        ("SaveCountAgain", 1),
        *((f"Reserved{Letter}", 0) for Letter in "JKLM"),
    )


# save shorts needs an explicit validity boundary so drawing objects retain valid ownership and reference relationships
def SaveShorts(VersionGuid: str) -> DwgRecord:
    try:
        Digits = UUID(VersionGuid.strip("{}")).bytes
    except ValueError as Failure:
        raise ValueError(
            f"Authored DWG version GUID {VersionGuid!r} is malformed"
        ) from Failure
    ShortValue = int.from_bytes(Digits[0:2], "little") or KShortFill
    return MakeFrame(18, int.from_bytes(ShortValue.to_bytes(2, "little"), "big"), b"")


# the rev history contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def RevHistory() -> DwgRecord:
    return MakeRecord(
        ("ReservedA", 0),
        ("ReservedB", 0),
        ("EntryCount", 1),
        ("Entries", (MakeRecord(("EntryValue", 0)),)),
    )


# the section vars contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def SectionVars(
    HandSeed: int, ObjectCount: int, Moment: DwgDayTime, VersionGuid: str
) -> tuple[tuple[str, DwgRecord], ...]:
    return (
        ("AcDb:Header", SaveShorts(VersionGuid)),
        ("AcDb:RevHistory", RevHistory()),
        ("AcDb:ObjFreeSpace", FreeSpace(ObjectCount, Moment)),
        ("AcDb:Template", MakeRecord(("Description", ""), ("Measurement", 1))),
        ("AcDb:AuxHeader", AuxHeader(HandSeed, Moment)),
    )
