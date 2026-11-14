from datetime import datetime as DateTime
from uuid import UUID

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorShell import (
    AuthorShell,
    KClassLead,
    ReplaceVars,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.FinishBook import FinishBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.PlaceDimension import (
    PlaceDimMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ResolveDraft import ResolveRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceSheet import (
    PlaceSheetMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import KLayoutKey
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ShellDefaults import (
    KAuthorVersion,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DwgDraft import DwgDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.HeaderPlan import (
    PlanHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.ClassPlan import (
    PlanClasses,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.PlaceApps import (
    PlaceAppsMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.PlaceNamed import (
    PlaceNamedMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.PlaceTables import (
    PlaceTablesMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.TableVocab import (
    KFixedHandles,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.PlaceViews import (
    PlaceViewsMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDayTime import DwgDayTime

KJulianShift = 1721425
KDayMilliSeconds = 86400000


def DayTime(Moment: DateTime) -> DwgDayTime:
    MilliSeconds = (
        (Moment.hour * 60 + Moment.minute) * 60 + Moment.second
    ) * 1000 + Moment.microsecond // 1000
    return DwgDayTime(
        Moment.toordinal() + KJulianShift, MilliSeconds % KDayMilliSeconds
    )


def GuidText(Value: str) -> str:
    try:
        return "{" + str(UUID(Value)).upper() + "}"
    except ValueError as Failure:
        raise ValueError(f"Authored DWG GUID {Value!r} is malformed") from Failure


def StartBook(Draft: DwgDraft) -> DraftBook:
    Fixed = dict(KFixedHandles)
    if Draft.LayoutHandle in Fixed.values() or Draft.LayoutHandle <= 0:
        raise ValueError(f"Authored DWG layout handle {Draft.LayoutHandle} is reserved")
    Fixed[KLayoutKey] = Draft.LayoutHandle
    Ledger = DraftBook(Fixed)
    Paper = SheetSize(Draft.Sheet.SheetSize)
    PlaceNamedMut(Ledger, Paper)
    PlaceTablesMut(Ledger, Paper)
    return Ledger


def AuthorDwg(Draft: DwgDraft) -> bytes:
    Ledger = StartBook(Draft)
    PlaceSheetMut(Ledger, Draft.Sheet)
    PlaceViewsMut(Ledger, Draft)
    for Index, Dimension in enumerate(Draft.Dimensions):
        _ = PlaceDimMut(Ledger, Index, Dimension)
    PlaceAppsMut(Ledger)
    Classes = PlanClasses(Ledger)
    Table = DwgClassTable(0, KClassLead, Classes, 0)
    Objects, Handles = FinishBook(Ledger, Table, KAuthorVersion)
    Moment = DayTime(Draft.Moment)
    HeaderVars = ReplaceVars(
        ResolveRecord(
            PlanHeader(SheetSize(Draft.Sheet.SheetSize)), Handles, Ledger.SlotItems
        ),
        {
            "FingerprintGuid": GuidText(Draft.FingerprintGuid),
            "VersionGuid": GuidText(Draft.VersionGuid),
            "TdCreateDay": Moment.DayNumber,
            "TdCreateMsec": Moment.MilliSeconds,
            "TdUpdateDay": Moment.DayNumber,
            "TdUpdateMsec": Moment.MilliSeconds,
        },
    )
    return AuthorShell(Objects, HeaderVars, Classes, Moment)
