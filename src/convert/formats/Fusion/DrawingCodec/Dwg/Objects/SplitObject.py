from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import (
    ReadHandleMut,
    ReadObjTypeMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadUnicodeMut import ReadUnicodeMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Classes.LocateStrings import (
    LocateStrings,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Handles.ReadUnsignedMc import (
    ReadUnsignedMc,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.ModularCodes import ReadModular


def SplitTexts(
    BodyValue: bytes, DataStart: int, DataBits: int
) -> tuple[tuple[str, ...], bool, int]:
    if BitCursor(BodyValue, DataBits - 1, DataBits).TakeBits(1) == 0:
        return (), False, DataBits - 1
    TextStart, TextFinish = LocateStrings(BodyValue, DataStart, DataBits)
    Cursor = BitCursor(BodyValue, TextStart, TextFinish)
    TextItems: list[str] = []
    while Cursor.Position < TextFinish:
        TextItems.append(ReadUnicodeMut(Cursor))
    return tuple(TextItems), True, TextStart


def SplitHandles(BodyValue: bytes, DataBits: int) -> tuple[DwgHandleRef, ...]:
    TotalBits = len(BodyValue) * 8
    Cursor = BitCursor(BodyValue, DataBits, TotalBits)
    HandleRefs: list[DwgHandleRef] = []
    while TotalBits - Cursor.Position >= 8:
        HandleRefs.append(ReadHandleMut(Cursor))
    Width = TotalBits - Cursor.Position
    if Cursor.TakeBits(Width) != (1 << Width) - 1:
        raise ValueError("DWG object handle stream padding is not all ones")
    return tuple(HandleRefs)


def SplitObject(DataValue: bytes, Offset: int) -> tuple[DwgObject, int]:
    BodySize, Position = ReadModular(DataValue, Offset)
    HandleBits, Position = ReadUnsignedMc(DataValue, Position)
    BodyValue = TakeSpan(DataValue, Position, BodySize, "object body")
    CrcValue = ReadFields(DataValue, Position + BodySize, "<H", "object CRC")[0]
    if CrcSixteen(0xC0C1, DataValue[Offset : Position + BodySize]) != CrcValue:
        raise ValueError(f"DWG object at {Offset:#x} CRC mismatch")
    DataBits = BodySize * 8 - HandleBits
    if not 0 < DataBits <= BodySize * 8:
        raise ValueError(f"DWG object at {Offset:#x} handle stream size is invalid")
    Cursor = BitCursor(BodyValue, 0, DataBits)
    TypeNumber = ReadObjTypeMut(Cursor)
    OwnRef = ReadHandleMut(Cursor)
    if OwnRef.RefCode != 0:
        raise ValueError(f"DWG object at {Offset:#x} has a relative own handle")
    TextItems, HasTexts, TextStart = SplitTexts(BodyValue, Cursor.Position, DataBits)
    TailWidth = TextStart - Cursor.Position
    TailValue = Cursor.TakeBits(TailWidth)
    HandleRefs = SplitHandles(BodyValue, DataBits)
    Empty = DwgRecord(())
    Generic = DwgObject(
        TypeNumber,
        OwnRef.RefValue,
        (),
        "",
        Empty,
        "",
        Empty,
        TailWidth,
        TailValue,
        TextItems,
        HasTexts,
        HandleRefs,
    )
    return Generic, Position + BodySize + 2
