# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import (
    KMaxMetaSize,
    KMaxMetaText,
)


# a bounded sink prevents oversized output even for otherwise valid typed values
class MetaSink:
    __slots__ = ("Buffer",)

    # a single mutable buffer avoids rebuilding the accumulated wire output
    def __init__(SinkValue) -> None:
        SinkValue.Buffer = bytearray()

    # bytes from any field share the same cumulative member limit
    def AddBytes(SinkValue, Content: bytes) -> None:
        if len(SinkValue.Buffer) + len(Content) > KMaxMetaSize:
            raise ValueError("Oversized Fusion MetaStream")
        SinkValue.Buffer.extend(Content)

    # unsigned word validation keeps invalid typed values out of struct packing
    def AddWord(SinkValue, Number: int) -> None:
        if type(Number) is not int or not 0 <= Number < 1 << 32:
            raise ValueError("Invalid Fusion MetaStream unsigned word")
        SinkValue.AddBytes(PackValue("<I", Number))

    # full width identities and offsets must survive synthetic construction unchanged
    def AddLong(SinkValue, Number: int) -> None:
        if type(Number) is not int or not 0 <= Number < 1 << 64:
            raise ValueError("Invalid Fusion MetaStream unsigned long")
        SinkValue.AddBytes(PackValue("<Q", Number))

    # text counts describe encoded units rather than unicode scalar values
    def AddText(SinkValue, Content: str, *, WideText: bool = False) -> None:
        if (
            type(Content) is not str
            or len(Content) > KMaxMetaText
            or not all(Letter.isprintable() for Letter in Content)
        ):
            raise ValueError("Invalid Fusion MetaStream string")
        DataValue = Content.encode("utf-16le" if WideText else "ascii")
        Count = len(DataValue) // (2 if WideText else 1)
        if Count > KMaxMetaText:
            raise ValueError("Oversized Fusion MetaStream string")
        SinkValue.AddWord(Count)
        SinkValue.AddBytes(DataValue)

    # sequence lengths are generated from immutable typed rows rather than copied bytes
    def AddCount(SinkValue, Items: tuple[object, ...], Maximum: int) -> None:
        if type(Items) is not tuple or len(Items) > Maximum:
            raise ValueError("Invalid Fusion MetaStream sequence")
        SinkValue.AddWord(len(Items))
