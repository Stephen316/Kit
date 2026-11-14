from uuid import UUID

from convert.formats.Fusion.DrawingCodec.Dwg.Author.ShellDefaults import (
    KProductKey,
    KProductText,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import MakeFrame
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppEntry import DwgAppEntry
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDayTime import DwgDayTime
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSummary import DwgSummary

KFreeMarks = (50, 100, 512, 0xFFFFFFFF)
KShortCount = 4
KShortFill = 0x5555
KAuxMarker = bytes.fromhex("ff8801")
KAuxVersion = (33, 285)
KAuxSaved = (22, 46)
KAuxCodes = (4, 1381, 0, 0, 0, 1, 0, 0, 0, 16843008, 65538)
KAuxNames = tuple(f"Code{Letter}" for Letter in "ABCDEF") + tuple(
    f"Reserved{Letter}" for Letter in "BCDEF"
)


def MakeRecord(*Pairs: tuple[str, KDwgValue]) -> DwgRecord:
    return DwgRecord(tuple(DwgField(Called, Value) for Called, Value in Pairs))


def AuthorSummary(Moment: DwgDayTime) -> DwgSummary:
    return DwgSummary(
        "", "", "", "", "", "", "", "", DwgDayTime(0, 0), Moment, Moment, (), (0, 0)
    )


def AuthorAppInfo() -> DwgAppInfo:
    return DwgAppInfo(3, "AppInfoDataList", (DwgAppEntry(KProductKey, KProductText),))


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


def SaveShorts(VersionGuid: str) -> DwgRecord:
    try:
        Digits = UUID(VersionGuid.strip("{}")).bytes
    except ValueError as Failure:
        raise ValueError(
            f"Authored DWG version GUID {VersionGuid!r} is malformed"
        ) from Failure
    TailBits = 0
    for Index in range(KShortCount):
        ShortValue = (
            int.from_bytes(Digits[2 * Index : 2 * Index + 2], "little") or KShortFill
        )
        TailBits = (TailBits << 18) | int.from_bytes(
            ShortValue.to_bytes(2, "little"), "big"
        )
    return MakeFrame(18 * KShortCount, TailBits, b"")


def RevHistory() -> DwgRecord:
    return MakeRecord(
        ("ReservedA", 0),
        ("ReservedB", 0),
        ("EntryCount", 1),
        ("Entries", (MakeRecord(("EntryValue", 0)),)),
    )


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
