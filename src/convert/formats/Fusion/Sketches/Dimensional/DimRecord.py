# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.RulePrefix import ReadRulePrefix


# the raw dimension retains both its typed parameter binding and ordered operand ids
@MakeDataClass(frozen=True, slots=True)
class NativeDimension:
    Code: int
    TargetIds: tuple[int, ...]
    BindingId: int
    PrefixSlot: int
    PrefixEnd: int
    BindingOffset: int


# byte slicing keeps each proof inside the exact primary native record
def DimRecordBody(BulkData: bytes, SpanValue: RecordSpan) -> bytes:
    Offset = SpanValue.PayloadOffset + 4
    if not 0 <= SpanValue.StartOffset < Offset <= SpanValue.EndOffset <= len(BulkData):
        raise ValueError("Fusion dimensional record has invalid bounds")
    return BulkData[Offset : SpanValue.EndOffset]


# repeated target copies establish the dimension operands without geometric inference
def ReadDimRecord(BodyValue: bytes) -> NativeDimension:
    Cursor = MetaCursor(BodyValue)
    Inputs, Slots, Attributes = ReadRulePrefix(Cursor)
    if (
        not 2 <= len(Inputs) <= 3
        or Inputs[0] != 0
        or Slots[0] == 0
        or any(Slots[1:])
        or set(Attributes) != {"EntityGenesis"}
        or type(Attributes["EntityGenesis"]) is not int
        or Attributes["EntityGenesis"] != 0
    ):
        raise ValueError(
            "Unsupported Fusion dimensional dependency or attribute layout"
        )
    Targets = Inputs[1:]
    if 0 in Targets or len(set(Targets)) != len(Targets):
        raise ValueError("Fusion dimensional operands are missing or ambiguous")
    PrefixEnd = Cursor.Offset
    BindingOffset = len(BodyValue) - (16 + 11 * len(Targets))
    if BindingOffset - 8 < PrefixEnd:
        raise ValueError("Fusion dimensional tail overlaps its prefix")
    Cursor.Offset = BindingOffset - 8
    CodeValue = Cursor.ReadLong()
    BindingId = ReadNativeRef(Cursor)
    if (
        BindingId == 0
        or Cursor.ReadWord() != len(Targets)
        or tuple(ReadNativeRef(Cursor) for _ in Targets) != Targets
    ):
        raise ValueError("Fusion dimensional binding or repeated operands disagree")
    if Cursor.TakeBytes(1) != b"\0" or Cursor.Offset != len(BodyValue):
        raise ValueError("Unsupported Fusion dimensional record trailer")
    return NativeDimension(
        CodeValue, Targets, BindingId, Slots[0], PrefixEnd, BindingOffset
    )
