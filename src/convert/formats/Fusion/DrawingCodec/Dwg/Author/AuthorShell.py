from collections import Counter
from dataclasses import replace as ReplaceFields

from convert.formats.Fusion.DrawingCodec.Dwg.Author.ShellDefaults import (
    KCryptHeader,
    KFileHeader,
    KMaxPageSize,
    KSectionRows,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ShellParts import (
    AuthorAppInfo,
    AuthorSummary,
    SectionVars,
)
from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import (
    EmitDwgFile,
    EncodeContents,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Image.PlanImages import ReplanFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDayTime import DwgDayTime
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import AsText
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.RecordParts import NamedValue

KClassLead = (0, 0, 1)


def ReplaceVars(Record: DwgRecord, Values: dict[str, KDwgValue]) -> DwgRecord:
    Names = {Entry.FieldName for Entry in Record.RecordFields}
    Missing = set(Values) - Names
    if Missing:
        raise ValueError(f"Authored DWG record lacks fields {sorted(Missing)}")
    return DwgRecord(
        tuple(
            DwgField(Entry.FieldName, Values.get(Entry.FieldName, Entry.FieldValue))
            for Entry in Record.RecordFields
        )
    )


def CountClasses(
    ClassRows: tuple[DwgClassRow, ...], Objects: tuple[DwgObject, ...]
) -> DwgClassTable:
    Counts = Counter(Member.ClassKind for Member in Objects)
    Entries = tuple(
        ReplaceFields(Entry, InstanceCount=Counts.get(Entry.DxfName, 0))
        for Entry in ClassRows
    )
    return DwgClassTable(
        max(Entry.ClassNumber for Entry in Entries), KClassLead, Entries, 0
    )


def SectionInfos() -> tuple[DwgSectionInfo, ...]:
    Leading = DwgSectionInfo("", 0, 0, 0, KMaxPageSize, 1, 2, 0, ())
    return (Leading,) + tuple(
        DwgSectionInfo(Called, Number, 0, 0, PageSize, 1, Compress, 0, ())
        for Called, Number, PageSize, Compress in KSectionRows
    )


def AuthorShell(
    Objects: tuple[DwgObject, ...],
    HeaderVars: DwgRecord,
    ClassRows: tuple[DwgClassRow, ...],
    Moment: DwgDayTime,
) -> bytes:
    HandSeed = max(Member.ObjectHandle for Member in Objects) + 1
    Infos = SectionInfos()
    Model = DwgFile(
        KFileHeader,
        KCryptHeader,
        (2, KMaxPageSize, 0, len(Infos)),
        Infos,
        (),
        (),
        ReplaceVars(HeaderVars, {"HandSeed": DwgHandleRef(0, HandSeed)}),
        CountClasses(ClassRows, Objects),
        Objects,
        AuthorSummary(Moment),
        AuthorAppInfo(),
        SectionVars(
            HandSeed,
            len(Objects),
            Moment,
            AsText(NamedValue(HeaderVars, "VersionGuid")),
        ),
        (),
    )
    return EmitDwgFile(ReplanFile(Model, EncodeContents(Model)))
