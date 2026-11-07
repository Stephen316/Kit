# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import unpack_from as UnpackFrom


# metadata reads share bounds checks to keep truncated fields inside their stream
class MetaCursor:

    # cursor state keeps sequential fields independent of caller slicing
    def __init__(self, DataValue: bytes) -> None:
        self.DataValue = DataValue
        self.Offset = 0

    # every field advances through one checked boundary
    def TakeBytes(self, Count: int) -> bytes:
        Finish = self.Offset + Count
        if Count < 0 or Finish > len(self.DataValue):
            raise ValueError("Truncated Fusion MetaStream")
        Result = self.DataValue[self.Offset : Finish]
        self.Offset = Finish
        return Result

    # stored counts and property values use the same unsigned width
    def ReadWord(self) -> int:
        return int(UnpackFrom("<I", self.TakeBytes(4))[0])

    # identifiers and offsets require the full native width
    def ReadLong(self) -> int:
        return int(UnpackFrom("<Q", self.TakeBytes(8))[0])

    # bound attacker controlled lists before allocating their contents
    def ReadCount(self, Maximum: int) -> int:
        Count = self.ReadWord()
        if Count > Maximum:
            raise ValueError("Fusion MetaStream count exceeds limit")
        return Count

    # string framing allows registry identities to be compared exactly
    def ReadText(
        self,
        WideText: bool = False,
        *,
        Maximum: int = 4096,
        AllowControls: bool = False,
    ) -> str:
        Length = self.ReadCount(Maximum)
        TextValue = self.TakeBytes(Length * (2 if WideText else 1)).decode(
            "utf-16le" if WideText else "ascii"
        )
        if not all(
            Letter.isprintable() or (AllowControls and Letter in "\r\n\t")
            for Letter in TextValue
        ):
            raise ValueError("Unprintable Fusion MetaStream string")
        return TextValue
