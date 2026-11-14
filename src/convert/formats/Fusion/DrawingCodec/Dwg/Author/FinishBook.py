from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed, DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.MakeObject import MakeObject
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ResolveDraft import (
    HandleOf,
    KSlotMap,
    ResolveRecord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ShapeRecord import ShapeRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgEed import DwgEed
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.FixedTypes import KFixedTypes

KFixedNumbers = {NameText: Number for Number, NameText in KFixedTypes.items()}
KFirstHandle = 0x10


def TypeNumberOf(ClassTable: DwgClassTable, ClassName: str) -> int:
    Number = KFixedNumbers.get(ClassName)
    if Number is not None:
        return Number
    for ClassRow in ClassTable.ClassRows:
        if ClassRow.DxfName == ClassName:
            return ClassRow.ClassNumber
    raise ValueError(f"Authored DWG class {ClassName!r} has no type number")


def AssignHandles(Ledger: DraftBook) -> dict[str, int]:
    KeyTexts = [Entry.KeyText for Entry in Ledger.DraftRows]
    if len(set(KeyTexts)) != len(KeyTexts):
        raise ValueError("Authored DWG places an object key twice")
    if not set(Ledger.FixedHandles) <= set(KeyTexts):
        raise ValueError("Authored DWG fixes a handle for an object it never places")
    Handles = dict(Ledger.FixedHandles)
    Taken = set(Handles.values())
    NextHandle = KFirstHandle
    for KeyText in KeyTexts:
        if KeyText in Handles:
            continue
        while NextHandle in Taken:
            NextHandle += 1
        Handles[KeyText] = NextHandle
        NextHandle += 1
    return Handles


def FinishEed(Block: DraftEed, Handles: Mapping[str, int], Slots: KSlotMap) -> DwgEed:
    AppRef = DwgHandleRef(
        Block.AppLink.RefCode, HandleOf(Handles, Block.AppLink.KeyText)
    )
    return DwgEed(AppRef, ResolveRecord(Block.EedItems, Handles, Slots), b"")


def FinishRow(
    Drafted: DraftRow,
    Handles: Mapping[str, int],
    Slots: KSlotMap,
    ClassTable: DwgClassTable,
    VersionText: str,
) -> DwgObject:
    Common = ResolveRecord(Drafted.CommonData, Handles, Slots)
    CommonKind = (
        "Entity"
        if any(Entry.FieldName == "HasGraphics" for Entry in Common.RecordFields)
        else "Object"
    )
    return MakeObject(
        TypeNumberOf(ClassTable, Drafted.ClassName),
        Handles[Drafted.KeyText],
        ShapeRecord(CommonKind, FieldMap(Common), VersionText, Drafted.SpareCommon),
        Drafted.ClassName,
        ShapeRecord(
            Drafted.ClassName,
            FieldMap(ResolveRecord(Drafted.ClassData, Handles, Slots)),
            VersionText,
            Drafted.SpareClass,
        ),
        VersionText,
        tuple(FinishEed(Block, Handles, Slots) for Block in Drafted.EedBlocks),
    )


def FieldMap(Record: DwgRecord) -> dict[str, KDwgValue]:
    return {Entry.FieldName: Entry.FieldValue for Entry in Record.RecordFields}


def FinishBook(
    Ledger: DraftBook, ClassTable: DwgClassTable, VersionText: str
) -> tuple[tuple[DwgObject, ...], dict[str, int]]:
    Handles = AssignHandles(Ledger)
    Objects = tuple(
        FinishRow(Entry, Handles, Ledger.SlotItems, ClassTable, VersionText)
        for Entry in Ledger.DraftRows
    )
    return tuple(sorted(Objects, key=HandleKey)), Handles


def HandleKey(Member: DwgObject) -> int:
    return Member.ObjectHandle
