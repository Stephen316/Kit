from dataclasses import dataclass as Dataclass
from typing import cast as CastValue

from DefinitionFragment import ReadDefinitionFragment
from DefinitionOptions import KDefinitionOptionsGeneration
from DefinitionStream import KBuildStamp, KPrimaryPlacement, KSessionWords
from JournalAttach import JournalAttach
from convert.adapters.solidworks.container import Definition as Fields
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)


# these fields vary independently of the shared class allocations and fixed settings
@Dataclass(frozen=True, slots=True)
class DefinitionReadback:
    UserName: str
    PreambleView: tuple[float, ...] | None
    Camera: tuple[float, float, float, float]
    Views: tuple[Fields.ViewRecord, Fields.ViewRecord, Fields.ViewRecord]
    Attachment: JournalAttach
    AppearanceCounter: int
    TerminalValue: float
    Bindings: tuple[Fields.LineFontBinding, ...]


# the optional preamble view changes the starting offset of the shared class map
def ReadPreamble(
    Cursor: FieldCursor,
) -> tuple[tuple[float, ...] | None, tuple[float, float, float, float]]:
    RequireArch(
        Cursor.ReadValue("<5I16s3s"),
        (
            Fields.KPreambleFlags,
            Fields.KPreambleGeneration,
            Fields.KPreambleFieldEight,
            Fields.KPreambleFieldOneTwo,
            Fields.KPreambleFieldOneSix,
            Fields.KPartClsid,
            Fields.KPreambleReserved,
        ),
        "Definition preamble part frame",
    )
    (Present,) = Cursor.ReadInts("<B")
    RequireArch(Present in (0, 1), True, "Definition preamble view presence")
    ViewValue = Cursor.ReadPoint(Fields.KViewBlockDoubles) if Present else None
    RequireArch(
        Cursor.ReadValue("<24sdH"),
        (Fields.KPreambleMiddle, Fields.KPreambleScale, Fields.KPreamblePad),
        "Definition preamble camera prefix",
    )
    Camera = CastValue(tuple[float, float, float, float], Cursor.ReadPoint(4))
    RequireArch(
        Cursor.ReadInts("<7H"), Fields.KPreambleTrailerWords, "Definition preamble tail"
    )
    return ViewValue, Camera


# the fixed style order proves each reference before the font manager takes custody
def ReadDrafting(Cursor: ArchiveCursor) -> None:
    _ = Cursor.TakePointer(("moBS_c",), KDefinitionKind)
    RequireArch(
        Cursor.ReadInts("<I"), (Fields.KDraftingStandardState,), "drafting state"
    )
    for Index, Style in enumerate(Fields.KLineStyles):
        _ = Cursor.TakePointer(
            (Fields.KLineStyleClass,), KClassRefKind if Index else KDefinitionKind
        )
        RequireArch(
            (Cursor.ReadText(), Cursor.ReadText(), Cursor.ReadInts("<H")),
            (Style.key, Style.display, (len(Style.segments),)),
            "Definition line style header",
        )
        RequireArch(
            (Cursor.ReadPoint(len(Style.segments)), Cursor.ReadInts("<B")),
            (Style.segments, (Style.flag,)),
            "Definition line style fields",
        )


# the annotation map has fixed bindings with more than one witnessed storage order
def ReadBindings(Cursor: ArchiveCursor) -> tuple[Fields.LineFontBinding, ...]:
    _ = Cursor.TakePointer((Fields.KLineFontManagerClass,), KDefinitionKind)
    (Count,) = Cursor.ReadInts("<H")
    RequireArch(Count, len(Fields.KLineFontBindings), "Definition line font count")
    Bindings = []
    for Index in range(Count):
        Annotation = Cursor.ReadText()
        _ = Cursor.TakePointer(
            (Fields.KLineFontConfigClass,), KClassRefKind if Index else KDefinitionKind
        )
        Font = Cursor.ReadText()
        Weight, Width, Tail = CastValue(
            tuple[int, float, int], Cursor.ReadValue("<hfh")
        )
        Bindings.append(Fields.LineFontBinding(Annotation, Font, Weight, Width, Tail))
    RequireArch(set(Bindings), set(Fields.KLineFontBindings), "Definition line fonts")
    RequireArch(
        Cursor.ReadInts("<H"),
        (Fields.KLineFontManagerTrailing,),
        "Definition font tail",
    )
    return tuple(Bindings)


# the primary view owns an untagged placement that the two secondary views omit
def ReadView(Cursor: FieldCursor, Primary: bool) -> Fields.ViewRecord:
    (Present,) = Cursor.ReadInts("<B")
    RequireArch(
        Present in (0, 1), True, "Definition environment view rotation presence"
    )
    Rotation = Cursor.ReadPoint(Fields.KViewBlockDoubles) if Present else ()
    Translation = CastValue(tuple[float, float, float], Cursor.ReadPoint(3))
    (Scale,) = Cursor.ReadPoint(1)
    (Gap,) = Cursor.ReadInts("<H")
    Centre = CastValue(tuple[float, float, float], Cursor.ReadPoint(3))
    (Height,) = Cursor.ReadPoint(1)
    Flag, First, Second = Cursor.ReadInts("<BHH")
    (Trailer,) = Cursor.ReadPoint(1)
    Name = Cursor.ReadText()
    if Primary:
        RequireArch(
            Cursor.ReadInts("<II6Hi"), KPrimaryPlacement, "Definition primary placement"
        )
    return Fields.ViewRecord(
        Rotation,
        Translation,
        Scale,
        Gap,
        Centre,
        Height,
        Flag,
        First,
        Second,
        Trailer,
        Name,
        Primary,
    )


# the saved part must traverse the owned archive fields before reading the journal tail
def ReadModernPartDefinition(BlobValue: bytes, Generation: int) -> DefinitionReadback:
    RequireArch(Generation, KDefinitionOptionsGeneration, "part Definition generation")
    Preamble = FieldCursor(BlobValue, 0)
    PreambleView, Camera = ReadPreamble(Preamble)
    Cursor = ArchiveCursor(
        BlobValue, Preamble.Offset, Fields.KFirstLoadArrayIndex, {}, {}
    )
    ReadDrafting(Cursor)
    Bindings = ReadBindings(Cursor)
    _ = Cursor.TakePointer((Fields.KUserModelEnvClass,), KDefinitionKind)
    UserName = Cursor.ReadText()
    RequireArch(Cursor.ReadInts("<8H"), KSessionWords, "Definition session words")
    Views = (ReadView(Cursor, True), ReadView(Cursor, False), ReadView(Cursor, False))
    RequireArch(
        Cursor.ReadValue("<12sI20siiIB"),
        (
            bytes(Fields.KEnvironmentReservedHead),
            Fields.KEnvironmentCapacity,
            bytes(Fields.KEnvironmentReservedMiddA),
            *Fields.KEnvironmentSentinels,
            KBuildStamp,
            Fields.KEnvironmentTrailingFlag,
        ),
        "Definition environment tail",
    )
    _ = Cursor.TakePointer((Fields.KBomManagerClass,), KDefinitionKind)
    Head, Build, Reserved, Flag, Tail = Fields.KManagerTailWords
    RequireArch(
        Cursor.ReadInts("<IHHIHHH"),
        (Fields.KBomInfoCount, Head, Build, Reserved, 0, Flag, Tail),
        "Definition empty BOM",
    )
    Attachment, Counter, Terminal = ReadDefinitionFragment(
        BlobValue, Cursor.Offset, Generation
    )
    return DefinitionReadback(
        UserName, PreambleView, Camera, Views, Attachment, Counter, Terminal, Bindings
    )
