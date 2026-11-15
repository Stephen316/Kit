from functools import partial as Partial

from convert.adapters.solidworks.config.AnnotationData import (
    ReadFinishData,
    ReadNoteData,
    ReadWeldData,
)
from convert.adapters.solidworks.config.Annotations import ReadAnnotDefs
from convert.adapters.solidworks.config.Detail import (
    KStyleTails,
    ReadDetailStart,
    ReadLengthCode,
    ReadStyleHead,
    ReadStyleTail,
)
from convert.adapters.solidworks.config.DetailEnd import ReadDetailEnd
from convert.adapters.solidworks.config.Labels import ReadLabelDefs
from convert.adapters.solidworks.config.ModelLists import ReadModelLists
from convert.adapters.solidworks.config.PointerReader import PointerReader
from convert.adapters.solidworks.config.Regions import (
    KRegionRow,
    ReadPartReturn,
    ReadRegions,
)
from convert.adapters.solidworks.config.Scene import (
    ReadEnvironment,
    ReadExplManager,
    ReadSketchBlock,
)
from convert.adapters.solidworks.config.Tables import ReadTableDefs
from convert.adapters.solidworks.config.Tolerance import ReadTolData
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import (
    ArchiveCursor,
    KArchiveEvent,
)


# native pointer observations depend on the cursor and counter before each token
def ReadModelTagMut(
    Cursor: ArchiveCursor,
    Events: list[KArchiveEvent],
    KindValue: str,
    NameValue: str | None = None,
    SchemaValue: int = 1,
) -> int:
    Offset, Counter = Cursor.Offset, Cursor.NextIndex
    TagValue, _, Index = Cursor.TakePointer((NameValue,), KindValue, SchemaValue)
    Events.append((Offset, Counter, TagValue.kind, NameValue, Index))
    return Index


# the matrix presence bit distinguishes transform records with different lengths
def ReadViewXform(Cursor: ArchiveCursor) -> None:
    (MatrixFlag,) = Cursor.ReadValue("<B")
    RequireArch(MatrixFlag in (0, 1), True, "view transform matrix flag")
    if MatrixFlag:
        _ = Cursor.ReadPoint(9)
    _ = Cursor.ReadPoint(4)
    RequireArch(Cursor.ReadValue("<B"), (0,), "view transform extension mode")


# the three optional view collections have no entries on the witnessed path
def ReadConfigView(Cursor: ArchiveCursor) -> str:
    ViewName = Cursor.ReadText()
    for _ in range(2):
        ReadViewXform(Cursor)
    _ = Cursor.ReadValue("<Hi")
    _ = Cursor.ReadPoint(1)
    RequireArch(Cursor.ReadCount(), 0, "empty view pointer array")
    _ = Cursor.ReadValue("<2i")
    RequireArch(Cursor.ReadCount(), 0, "empty first view list")
    _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadPoint(1)
    RequireArch(Cursor.ReadCount(), 0, "empty second view list")
    _ = Cursor.ReadValue("<2i")
    return ViewName


# the style selects an absent or inline dual unit from the actual archive tag
def ReadLengthLink(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    if ReadTag(Cursor.BlobValue, Cursor.Offset).kind == KNullKind:
        _ = ReadPointer(KNullKind)
        return
    _ = ReadPointer(KClassRefKind, "moLengthUserUnits_c")
    ReadLengthCode(Cursor)
    _ = ReadPointer(KNullKind)


# the annotation subtype reads its inline view base before its nullable references
def ReadAnnotView(
    Cursor: ArchiveCursor, ReadPointer: PointerReader, NameValues: tuple[str, ...]
) -> None:
    RequireArch(
        ReadConfigView(Cursor) in NameValues, True, "witnessed annotation view name"
    )
    _ = Cursor.ReadValue("<i")
    _ = ReadPointer(KNullKind)
    _ = ReadPointer(KNullKind)
    _ = Cursor.ReadValue("<id")
    _ = ReadPointer(KNullKind)
    _ = Cursor.ReadValue("<2i")
    _ = ReadPointer(KNullKind)
    _ = Cursor.ReadValue("<4i")


# inline detail records share the model map when their length units allocate
def ReadSavedDetail(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    ReadDetailStart(Cursor)
    for Format in KStyleTails:
        ReadStyleHead(Cursor)
        ReadLengthCode(Cursor)
        ReadLengthLink(Cursor, ReadPointer)
        ReadStyleTail(Cursor, Format)
    ReadAnnotDefs(Cursor)
    ReadTableDefs(Cursor)
    ReadLabelDefs(Cursor)
    ReadFinishData(Cursor)
    ReadNoteData(Cursor)
    ReadWeldData(Cursor)
    ReadTolData(Cursor, Partial(ReadPointer, KNullKind))
    ReadDetailEnd(Cursor)
    RequireArch(Cursor.ReadValue("<H"), (0,), "empty shared parameter array")


# view allocations must reuse classes declared earlier in the same archive
def ReadSavedViews(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    _ = ReadPointer(KNullKind)
    ListKind = (
        KClassRefKind if "suObList" in Cursor.Classes.values() else KDefinitionKind
    )
    _ = ReadPointer(ListKind, "suObList")
    RequireArch(Cursor.ReadValue("<H"), (0,), "empty leading view list")
    _ = ReadPointer(KDefinitionKind, "moView_c")
    _ = ReadConfigView(Cursor)
    for _ in range(9):
        _ = ReadPointer(KClassRefKind, "moView_c")
        _ = ReadConfigView(Cursor)
    _ = Cursor.ReadValue("<B2i")
    _ = ReadPointer(KDefinitionKind, "moFeatColorTab_c", 0)
    RequireArch(Cursor.ReadCount(), 0, "empty feature color table")
    _ = ReadPointer(KNullKind)
    _ = Cursor.ReadValue("<i")
    RequireArch(Cursor.ReadCount(), 0, "absent inline model node list")
    _ = Cursor.ReadValue("<i")


# the saved view list count governs which annotation objects can allocate
def ReadSavedAnnots(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    _ = ReadPointer(KClassRefKind, "suObList")
    (AnnotationCount,) = Cursor.ReadValue("<H")
    RequireArch(AnnotationCount in (1, 2), True, "witnessed annotation view count")
    _ = ReadPointer(KDefinitionKind, "moAnnotationView_c")
    ReadAnnotView(Cursor, ReadPointer, ("*Front", "*Right"))
    if AnnotationCount == 2:
        _ = ReadPointer(KClassRefKind, "moAnnotationView_c")
        ReadAnnotView(Cursor, ReadPointer, ("*Top",))


# a model map is usable only after the typed presentation path reaches stream end
def ReadModelTail(
    Cursor: ArchiveCursor,
) -> tuple[list[KArchiveEvent], list[list[KRegionRow]]]:
    Events: list[KArchiveEvent] = []
    ReadPointer = Partial(ReadModelTagMut, Cursor, Events)
    ReadSavedDetail(Cursor, ReadPointer)
    ReadEnvironment(Cursor, ReadPointer)
    ReadSavedViews(Cursor, ReadPointer)
    ReadSketchBlock(Cursor, ReadPointer)
    ReadSavedAnnots(Cursor, ReadPointer)
    ReadModelLists(Cursor, ReadPointer)
    Regions = ReadRegions(Cursor)
    ReadExplManager(Cursor, ReadPointer)
    ReadPartReturn(Cursor)
    RequireArch(
        Cursor.Offset, len(Cursor.BlobValue), "complete witnessed Config-0 extent"
    )
    return Events, Regions
