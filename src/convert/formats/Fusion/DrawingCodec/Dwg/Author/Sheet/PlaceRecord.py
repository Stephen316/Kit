from typing import cast as CastValue

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import SoftPointer
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    DraftRecord,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.GroupItems import EncodeGroups

# the group items shape must stay shared so drawing sheet authoring uses one contract for compatible values
KGroupItems = tuple[tuple[str, KDraftValue], ...]


# the plain group contract needs a shared interpretation so paper layouts retain consistent object ownership
def PlainGroup(Value: KDraftValue) -> KDwgValue:
    if isinstance(Value, DraftLink):
        return 0
    return CastValue(KDwgValue, Value)


# the group size contract needs a stable decomposition so paper layouts retain consistent object ownership
def GroupSize(GroupItems: KGroupItems) -> int:
    Plain = tuple(DwgField(Group, PlainGroup(Value)) for Group, Value in GroupItems)
    return len(EncodeGroups(DwgRecord(Plain)))


# the record operation needs a consistent construction rule so paper layouts retain consistent object ownership
def PlaceRecordMut(
    Ledger: DraftBook, KeyText: str, FolderKey: str, GroupItems: KGroupItems
) -> str:
    return PlaceMut(
        Ledger,
        KeyText,
        "XRECORD",
        {"Owner": SoftPointer(FolderKey), "Reactors": (SoftPointer(FolderKey),)},
        {"DataSize": GroupSize(GroupItems), "Items": DraftRecord(GroupItems)},
    )


# the byte groups contract needs a shared interpretation so paper layouts retain consistent object ownership
def ByteGroups(Payload: bytes) -> KGroupItems:
    return tuple(("70", Value) for Value in Payload)
