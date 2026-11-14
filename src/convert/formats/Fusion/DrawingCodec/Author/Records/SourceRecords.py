from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KBaseColumns,
    KTitleBlockId,
    KZeroGuid,
)
from convert.formats.Fusion.DrawingCodec.Author.Defaults.PartColumns import (
    KPartColumns,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.ColumnIdent import ColumnIdent
from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget
from convert.formats.Fusion.DrawingCodec.Author.Model.PartColumn import PartColumn
from convert.formats.Fusion.DrawingCodec.Author.Records.RecordIds import RecordIds
from convert.formats.Fusion.DrawingCodec.Author.Records.RecordTools import (
    ChildTail,
    MakeRecord,
    ObjectTail,
)
from convert.formats.Fusion.DrawingCodec.Model.CheckDatabase import KFileClass
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KSheetsGuid = "D67E6C0E-1316-4EF5-8967-9ACE29B9DF61"

KSheetGuid = "632EEBFC-0412-4AA4-9CF1-69C94F55C038"

KSourceGuid = "3EAD2723-67C3-4C8E-9B9E-1208F04C4C44"
KSourcesGuid = "658C29F4-1479-4B3E-AC06-7028B0BD003E"
KPartsGuid = "DFDD9951-64B7-4760-AA32-0543FD74B80F"
KModelSources = 25
KSheetFolder = 26
KDrawingRoot = 23
KSourceKind = "_Component"

KFilterValue: ValueObject[KEntityValue] = ValueObject(
    (
        EntityGroup(
            "62B5B83C-EDDB-483D-BCBD-1DB17B8386F0",
            (
                NamedValue("compFilterStr", ""),
                NamedValue("comps", ValueMap(())),
                NamedValue("isExtra", False),
            ),
        ),
    )
)


def FileRecord(FileName: str) -> EntityRecord:
    return MakeRecord(
        22,
        (EntityGroup(KFileClass, (NamedValue("persistedFileName", FileName),)),),
        RootId="ExternalDWG",
    )


def TrackedRoot(FirstIds: tuple[int, ...]) -> EntityRecord:
    Children = tuple(LocalRef(ObjectId) for ObjectId in FirstIds)
    return MakeRecord(24, ChildTail(None, Children), IsPrimary=False)


def SheetsRecord(SheetId: str, Planned: RecordIds) -> tuple[EntityRecord, ...]:
    Fields = (NamedValue("activeSheetId", SheetId), NamedValue("sketchIndex", 0))
    Children = tuple(LocalRef(ObjectId) for ObjectId in Planned.Sheets)
    return (
        MakeRecord(KSheetFolder, (EntityGroup(KSheetsGuid, Fields),)),
        MakeRecord(
            KSheetFolder,
            ChildTail(LocalRef(KDrawingRoot), Children),
            IsPrimary=False,
        ),
    )


def SourcesRecord(Planned: RecordIds) -> tuple[EntityRecord, ...]:
    Fields: tuple[NamedValue[KEntityValue], ...] = (
        NamedValue("DesignDocumentIdAndHashCode", ValueMap(())),
        NamedValue("designNextId", 1),
        NamedValue("lastUsedModelSource", LocalRef(Planned.Sources[-1])),
        NamedValue("modelSourceNextId", len(Planned.Sources) + 1),
    )
    Children = tuple(LocalRef(ObjectId) for ObjectId in Planned.Sources)
    return (
        MakeRecord(KModelSources, (EntityGroup(KSourcesGuid, Fields),)),
        MakeRecord(
            KModelSources,
            ChildTail(LocalRef(KDrawingRoot), Children),
            IsPrimary=False,
        ),
    )


def SourceParts(ObjectId: int) -> tuple[EntityRecord, ...]:
    return (
        MakeRecord(ObjectId, ObjectTail(LocalRef(KModelSources)), IsPrimary=False),
        MakeRecord(ObjectId + 1, (EntityGroup(KPartsGuid, ()),)),
        MakeRecord(ObjectId + 1, ChildTail(LocalRef(ObjectId)), IsPrimary=False),
    )


def SheetRecord(
    SheetId: str, SheetName: str, Design: DesignTarget, ObjectId: int, TabOrder: int
) -> tuple[EntityRecord, ...]:
    Fields = (
        NamedValue("componentOccPath", f"R{Design.ComponentId}-"),
        NamedValue("displayName", SheetName),
        NamedValue("isDisassociated", False),
        NamedValue("isOutOfDate", False),
        NamedValue("largeThumbnail", SheetId + "_large.png"),
        NamedValue("sheetId", SheetId),
        NamedValue("sheetOrder", TabOrder),
        NamedValue("thumbnail", SheetId + "_small.png"),
        NamedValue("titleBlockDesignId", KTitleBlockId),
        NamedValue("titleBlockOccPath", "root"),
        NamedValue("titleBlockPropertyOverriden", False),
    )
    return (
        MakeRecord(ObjectId, (EntityGroup(KSheetGuid, Fields),)),
        MakeRecord(ObjectId, ObjectTail(LocalRef(KSheetFolder)), IsPrimary=False),
    )


def SourceRecord(
    SheetId: str,
    LinkRole: str,
    Design: DesignTarget,
    PropertyColumns: bool,
    ObjectId: int,
    SourceIndex: int,
) -> EntityRecord:
    Owner = (Design.InstanceId, Design.ComponentId)
    Visible: ValueMap[KEntityValue] = ValueMap(
        (
            ValuePair(ValueSeries((*Owner, Design.BodiesId)), True),
            ValuePair(ValueSeries((*Owner, Design.SketchesId)), False),
        )
    )
    Fields: tuple[NamedValue[KEntityValue], ...] = (
        NamedValue("animationMarker", ValuePair("", 0.0)),
        NamedValue("bodyVisMap", Visible),
        NamedValue("designAssetGuid", KZeroGuid),
        NamedValue("designId", 1),
        NamedValue("index", SourceIndex),
        NamedValue("isComponentFilterUpdated", True),
        NamedValue("modelDocLinkName", LinkRole),
        NamedValue("newComponentFilter", KFilterValue),
        NamedValue("partsListColumns", SourceColumns(PropertyColumns)),
        NamedValue("partsLists", LocalRef(ObjectId + 1)),
        NamedValue("partslistType", 0),
        NamedValue("referenceDesignatorsList", None),
        NamedValue("sheetIds", ValueSeries((SheetId,))),
        NamedValue("silkscreenBodiesVisMap", ValueMap(())),
        NamedValue("silkscreensList", ValueMap(())),
        NamedValue("sourceComponentOccPathStr", ""),
        NamedValue("sourceId", f"{SourceIndex}{KSourceKind}"),
        NamedValue("sourceType", 4),
    )
    return MakeRecord(ObjectId, (EntityGroup(KSourceGuid, Fields),))


def SourceColumns(PropertyColumns: bool) -> ValueSeries[KEntityValue]:
    Columns = KPartColumns[:KBaseColumns]
    if PropertyColumns:
        Columns += tuple(sorted(KPartColumns[KBaseColumns:], key=ColumnName))
    return ValueSeries(
        tuple(ValuePair(ColumnIdent(Column), Column.Shown) for Column in Columns)
    )


def ColumnName(Column: PartColumn) -> str:
    return Column.DisplayName
