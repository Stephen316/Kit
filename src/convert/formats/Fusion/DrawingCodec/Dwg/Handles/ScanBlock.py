from convert.formats.Fusion.DrawingCodec.Dwg.Handles.ReadSignedMc import ReadSignedMc
from convert.formats.Fusion.DrawingCodec.Dwg.Handles.ReadUnsignedMc import (
    ReadUnsignedMc,
)


def ScanBlock(BlockBody: bytes, LastHandle: int, ObjectSize: int) -> tuple[int, int]:
    Position = 2
    HandleValue = 0
    Location = 0
    PairCount = 0
    Latest = LastHandle
    while Position < len(BlockBody):
        HandleStep, Position = ReadUnsignedMc(BlockBody, Position)
        LocationStep, Position = ReadSignedMc(BlockBody, Position)
        HandleValue += HandleStep
        Location += LocationStep
        if HandleValue <= Latest:
            raise ValueError("DWG handle map handles are not strictly increasing")
        if not 0 <= Location < ObjectSize:
            raise ValueError("DWG handle map location lies outside AcDb:AcDbObjects")
        Latest = HandleValue
        PairCount += 1
    return PairCount, Latest
