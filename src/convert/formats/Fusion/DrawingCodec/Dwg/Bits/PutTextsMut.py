from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import PutUnicodeMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import PutRawShortMut


def PutTextsMut(Writer: BitWriter, TextItems: tuple[str, ...], HasTexts: bool) -> None:
    if not HasTexts:
        if TextItems:
            raise ValueError("DWG string stream holds text but is flagged absent")
        Writer.PutBits(0, 1)
        return
    TextWriter = BitWriter()
    for TextValue in TextItems:
        PutUnicodeMut(TextWriter, TextValue)
    Writer.PutBits(TextWriter.BitValue, TextWriter.BitCount)
    StreamSize = TextWriter.BitCount
    if StreamSize >= 0x8000:
        PutRawShortMut(Writer, StreamSize >> 15)
        PutRawShortMut(Writer, StreamSize & 0x7FFF | 0x8000)
    else:
        PutRawShortMut(Writer, StreamSize)
    Writer.PutBits(1, 1)
