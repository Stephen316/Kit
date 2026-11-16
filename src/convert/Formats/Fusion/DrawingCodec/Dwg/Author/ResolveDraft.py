from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    DraftRecord,
    DraftSlot,
    KDraftValue,
    KHandleNumber,
    KSlotBytes,
    KSlotCount,
    KSlotFirst,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)

# the slot map shape must stay shared so native drawing authoring uses one contract for compatible values
KSlotMap = Mapping[str, Sequence[KDraftValue]]

# byte limit needs one explicit bound so native drawing authoring cannot accept inconsistent resource or layout limits
KByteLimit = 255

# null pointer must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KNullPointer = DwgHandleRef(4, 0)


# handle of needs an explicit validity boundary so drawing objects retain valid ownership and reference relationships
def HandleOf(Handles: Mapping[str, int], KeyText: str) -> int:
    Handle = Handles.get(KeyText)
    if Handle is None:
        raise ValueError(f"Authored DWG link {KeyText!r} names no placed object")
    return Handle


# resolve slot needs an explicit validity boundary so drawing objects retain valid ownership and reference relationships
def ResolveSlot(
    Value: DraftSlot, Handles: Mapping[str, int], Slots: KSlotMap
) -> KDwgValue:
    Items = Slots.get(Value.SlotName)
    if Items is None:
        raise ValueError(f"Authored DWG slot {Value.SlotName!r} is not declared")
    if Value.SlotForm == KSlotCount:
        return len(Items)
    if Value.SlotForm == KSlotFirst:
        return ResolveDraft(Items[0], Handles, Slots) if Items else KNullPointer
    if Value.SlotForm == KSlotBytes:
        return bytes([KByteLimit] * (len(Items) // KByteLimit)) + bytes(
            [len(Items) % KByteLimit] if len(Items) % KByteLimit else []
        )
    return ResolveDraft(tuple(Items), Handles, Slots)


# the resolve record contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def ResolveRecord(
    Value: DraftRecord, Handles: Mapping[str, int], Slots: KSlotMap
) -> DwgRecord:
    return DwgRecord(
        tuple(
            DwgField(FieldName, ResolveDraft(FieldValue, Handles, Slots))
            for FieldName, FieldValue in Value.DraftFields
        )
    )


# the resolve draft contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def ResolveDraft(
    Value: KDraftValue, Handles: Mapping[str, int], Slots: KSlotMap
) -> KDwgValue:
    if isinstance(Value, DraftLink) and Value.RefCode == KHandleNumber:
        return HandleOf(Handles, Value.KeyText)
    if isinstance(Value, DraftLink):
        return DwgHandleRef(Value.RefCode, HandleOf(Handles, Value.KeyText))
    if isinstance(Value, DraftSlot):
        return ResolveSlot(Value, Handles, Slots)
    if isinstance(Value, DraftRecord):
        return ResolveRecord(Value, Handles, Slots)
    if isinstance(Value, tuple):
        Items = tuple(ResolveDraft(Element, Handles, Slots) for Element in Value)
        return CastValue(KDwgValue, Items)
    return Value
