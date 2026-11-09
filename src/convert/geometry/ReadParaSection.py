# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import unpack_from as UnpackFrom
from convert.geometry.ParaFraming import KWrapperMagic
from convert.geometry.ParaFormatError import ParaFormatError
from convert.geometry.ParaSection import ParaSection
from convert.geometry.InflateFrame import InflateFrame
from convert.geometry.SectionBounds import SectionBounds


def ReadParaSection(DataValue: bytes, MagicOffset: int, SizeLimit: int) -> ParaSection:
    FrameStart = MagicOffset + len(KWrapperMagic)
    SectionEnd, Chained = SectionBounds(DataValue, MagicOffset)
    Cursor = FrameStart
    Decoded = bytearray()
    CompressedSize = 0
    while Cursor < SectionEnd:
        if Chained and not any(memoryview(DataValue)[Cursor:SectionEnd]):
            Cursor = SectionEnd
            break
        if Cursor + 8 > SectionEnd:
            raise ParaFormatError("truncated Parasolid frame header")
        RawSize, ZipSize = UnpackFrom("<II", DataValue, Cursor)
        ZipStart = Cursor + 8
        ZipEnd = ZipStart + ZipSize
        if not RawSize or not ZipSize:
            raise ParaFormatError("empty Parasolid frame")
        if ZipEnd > SectionEnd:
            raise ParaFormatError("truncated Parasolid frame payload")
        if RawSize > SizeLimit - len(Decoded):
            raise ParaFormatError("Parasolid decoded size limit exceeded")
        Decoded.extend(InflateFrame(DataValue[ZipStart:ZipEnd], RawSize))
        CompressedSize += ZipSize
        Cursor = ZipEnd
        if not Chained:
            break
    if not Decoded:
        raise ParaFormatError("empty Parasolid chain section")
    return ParaSection(
        bytes(Decoded),
        MagicOffset - 4 if Chained else MagicOffset,
        Cursor,
        FrameStart + 8,
        CompressedSize,
    )
