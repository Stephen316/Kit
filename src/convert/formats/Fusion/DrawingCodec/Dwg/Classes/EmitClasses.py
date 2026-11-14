from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import (
    PutBitLongMut,
    PutBitShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import PutRawCharMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutTextsMut import PutTextsMut
from convert.formats.Fusion.DrawingCodec.Dwg.Classes.CheckClassFrame import (
    KClassFinish,
    KClassStart,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader

KClassTrail = bytes(8)


def PutClassRowMut(Writer: BitWriter, Texts: list[str], ClassRow: DwgClassRow) -> None:
    PutBitShortMut(Writer, ClassRow.ClassNumber)
    PutBitShortMut(Writer, ClassRow.ProxyFlags)
    Texts.extend((ClassRow.AppName, ClassRow.CppName, ClassRow.DxfName))
    Writer.PutBits(1 if ClassRow.WasZombie else 0, 1)
    PutBitShortMut(Writer, ClassRow.ItemClassId)
    for Value in (
        ClassRow.InstanceCount,
        ClassRow.DwgVersion,
        ClassRow.MaintVersion,
        ClassRow.ReservedFirst,
        ClassRow.ReservedSecond,
    ):
        PutBitLongMut(Writer, Value)


def EmitClasses(ClassTable: DwgClassTable, FileHeader: DwgFileHeader) -> bytes:
    HasHighWord = (
        FileHeader.VersionText == "AC1032" or FileHeader.MaintenanceVersion > 3
    )
    Writer = BitWriter()
    Texts: list[str] = []
    PutBitShortMut(Writer, ClassTable.MaxClassNumber)
    PutRawCharMut(Writer, ClassTable.LeadCodes[0])
    PutRawCharMut(Writer, ClassTable.LeadCodes[1])
    Writer.PutBits(ClassTable.LeadCodes[2], 1)
    for ClassRow in ClassTable.ClassRows:
        PutClassRowMut(Writer, Texts, ClassRow)
    PutTextsMut(Writer, tuple(Texts), True)
    BitSize = Writer.BitCount + 32
    Padding = -Writer.BitCount & 7
    Writer.PutBits((1 << Padding) - 1, Padding)
    AreaValue = PackFields("<I", BitSize) + Writer.ToBytes()
    Covered = PackFields("<I", len(AreaValue)) + (bytes(4) if HasHighWord else b"")
    Covered += AreaValue
    CrcValue = PackFields("<H", CrcSixteen(0xC0C1, Covered))
    return KClassStart + Covered + CrcValue + KClassFinish + KClassTrail
