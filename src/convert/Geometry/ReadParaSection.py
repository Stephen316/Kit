from struct import unpack_from as UnpackFrom
from convert.Geometry.ParaFraming import KWrapperMagic
from convert.Geometry.ParaFormatError import ParaFormatError
from convert.Geometry.ParaSection import ParaSection
from convert.Geometry.InflateFrame import InflateFrame
from convert.Geometry.SectionBounds import SectionBounds


# the para section operation needs a distinct decoding boundary so native geometry retains a consistent interchange interpretation
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


# exact consecutive frames prevent the generic magic scanner from overlooking opaque bytes
def ReadEmptyFrame(
    Partition: bytes, StartOffset: int, PayloadSize: int
) -> ParaSection | None:
    MagicOffset = StartOffset + 4
    if Partition[MagicOffset : MagicOffset + len(KWrapperMagic)] != KWrapperMagic:
        return None
    try:
        Section = ReadParaSection(Partition, MagicOffset, PayloadSize)
    except ParaFormatError:
        return None
    FrameEnd = Section.CompressedOffset + Section.CompressedSize
    if (
        Section.Start != StartOffset
        or len(Section.Data) != PayloadSize
        or Section.End != FrameEnd + 8
        or Partition[FrameEnd : Section.End] != bytes(8)
    ):
        return None
    return Section
