from struct import unpack_from as UnpackFrom
from convert.geometry.ParaFraming import KWrapperMagic
from convert.geometry.ParaFormatError import ParaFormatError


def SectionBounds(DataValue: bytes, MagicOffset: int) -> tuple[int, bool]:
    if MagicOffset >= 4:
        ChainSize = UnpackFrom("<I", DataValue, MagicOffset - 4)[0]
        if ChainSize >= len(KWrapperMagic) + 8 and (
            ChainSize <= len(DataValue) - MagicOffset or MagicOffset == 4
        ):
            SectionEnd = MagicOffset + ChainSize
            if SectionEnd > len(DataValue):
                raise ParaFormatError("truncated Parasolid chain section")
            return SectionEnd, True
    return len(DataValue), False
