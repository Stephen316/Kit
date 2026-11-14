from convert.formats.Fusion.DrawingCodec.Author.Defaults.ContainerRecords import (
    KContainerRecords,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Author.Records.ComponentRecords import (
    ComponentRecord,
    InstanceRecord,
)
from convert.formats.Fusion.DrawingCodec.Author.Records.RecordIds import (
    PlanIds,
    RecordIds,
)
from convert.formats.Fusion.DrawingCodec.Author.Records.SourceRecords import (
    FileRecord,
    SheetRecord,
    SheetsRecord,
    SourceParts,
    SourceRecord,
    SourcesRecord,
    TrackedRoot,
)
from convert.formats.Fusion.DrawingCodec.Author.Records.TrackedRecords import (
    TrackedRecords,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KFirstSheetTab,
)
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


def DesignRecords(
    SpecValue: DrawingSpec, FileName: str, History: SaveState
) -> tuple[EntityRecord, ...]:
    Planned = SpecIds(SpecValue)
    SheetId = SheetHandle(SpecValue.LayoutHandle)
    LinkRole = SpecValue.Identity.LinkRole
    (SourceId,), (SheetIdent,) = Planned.Sources, Planned.Sheets
    Built = [
        ComponentRecord(SpecValue.Identity, History.CycleColor),
        InstanceRecord(SpecValue.Identity, History.InstanceGates),
        FileRecord(FileName),
        TrackedRoot(Planned.Tracked),
        *SourcesRecord(Planned),
        *SheetsRecord(SheetId, Planned),
        SourceRecord(
            SheetId,
            LinkRole,
            SpecValue.Design,
            History.PropertyColumns,
            SourceId,
            1 + Planned.Sources.index(SourceId),
        ),
        *SourceParts(SourceId),
        *SheetRecord(
            SheetId,
            SpecValue.Sheet.SheetName,
            SpecValue.Design,
            SheetIdent,
            KFirstSheetTab,
        ),
    ]
    for FirstId, EdgeValue in zip(Planned.Tracked, SpecValue.Annotations, strict=True):
        Built.extend(TrackedRecords(FirstId, EdgeValue, SpecValue.Design))
    return tuple(sorted((*KContainerRecords, *Built), key=RecordKey))


def RecordKey(Record: EntityRecord) -> tuple[int, bool]:
    return Record.ObjectId, not Record.IsPrimary


def SheetHandle(LayoutHandle: int) -> str:
    return f"{LayoutHandle:X}"


def SpecIds(SpecValue: DrawingSpec) -> RecordIds:
    return PlanIds(1, 1, SpecValue.Annotations)


def DesignNextId(SpecValue: DrawingSpec, History: SaveState) -> int:
    NextFree = SpecIds(SpecValue).NextFree
    if History.DesignNextId is None:
        return NextFree
    if type(History.DesignNextId) is not int or History.DesignNextId < NextFree:
        raise ValueError("Fusion drawing next identity collides with its records")
    return History.DesignNextId
