from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Handles.ScanBlock import ScanBlock
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleMap import DwgHandleMap


def CountHandles(DataValue: bytes, ObjectSize: int) -> DwgHandleMap:
    Offset = 0
    HandleCount = 0
    LastHandle = 0
    BlockCount = 0
    BlockSize = 0
    while BlockSize != 2:
        BlockSize = ReadFields(DataValue, Offset, ">H", "handle block size")[0]
        if BlockSize < 2:
            raise ValueError("DWG handle block size is smaller than its size field")
        BlockBody = TakeSpan(DataValue, Offset, BlockSize, "handle block")
        CrcOffset = Offset + BlockSize
        CrcValue = ReadFields(DataValue, CrcOffset, ">H", "handle block CRC")[0]
        if CrcSixteen(0xC0C1, BlockBody) != CrcValue:
            raise ValueError(f"DWG handle block {BlockCount} CRC mismatch")
        PairCount, LastHandle = ScanBlock(BlockBody, LastHandle, ObjectSize)
        HandleCount += PairCount
        BlockCount += 1
        Offset += BlockSize + 2
    if Offset != len(DataValue):
        raise ValueError("DWG handle map has unexpected trailing bytes")
    return DwgHandleMap(HandleCount, LastHandle, BlockCount)
