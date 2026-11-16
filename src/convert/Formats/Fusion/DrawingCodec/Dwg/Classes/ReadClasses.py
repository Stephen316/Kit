from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitMut import ReadBitMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitShortMut import (
    ReadBitShortMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawCharMut import ReadRawCharMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.Formats.Fusion.DrawingCodec.Dwg.Classes.CheckClassFrame import (
    CheckClassFrame,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Classes.LocateStrings import (
    LocateStrings,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Classes.ReadRowsMut import ReadRowsMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader


# the classes operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadClasses(DataValue: bytes, FileHeader: DwgFileHeader) -> DwgClassTable:
    HasHighWord = (
        FileHeader.VersionText == "AC1032" or FileHeader.MaintenanceVersion > 3
    )
    DataStart = 24 if HasHighWord else 20
    AreaSize = ReadFields(DataValue, 16, "<I", "class data size")[0]
    if HasHighWord and ReadFields(DataValue, 20, "<I", "class size high word")[0]:
        raise ValueError("DWG class section size exceeds 32 bits")
    BitSize = ReadFields(DataValue, DataStart, "<I", "class bit size")[0]
    CrcValue = CheckClassFrame(DataValue, DataStart + AreaSize)
    if not 64 <= BitSize <= AreaSize * 8:
        raise ValueError("DWG class bit size is inconsistent with the class data size")
    StringStart, StringFinish = LocateStrings(
        DataValue, DataStart * 8 + 32, DataStart * 8 + BitSize
    )
    MainCursor = BitCursor(DataValue, DataStart * 8 + 32, StringStart)
    TextCursor = BitCursor(DataValue, StringStart, StringFinish)
    MaxClassNumber = ReadBitShortMut(MainCursor)
    LeadCodes = (
        ReadRawCharMut(MainCursor),
        ReadRawCharMut(MainCursor),
        ReadBitMut(MainCursor),
    )
    return DwgClassTable(
        MaxClassNumber, LeadCodes, ReadRowsMut(MainCursor, TextCursor), CrcValue
    )
