from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmPtr,
    RequireAsm,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmPrism import ReadAsmShell
from convert.Formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse, ReadAsmRim
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# current blind and through all bodies have distinct owned face and hole inventories
def ReadResultRims(
    Table: AsmTable, BodyIndex: int, FaceCount: int
) -> dict[int, tuple[AsmUse, ...]]:
    ShellId, FaceId = ReadAsmShell(Table, BodyIndex, AllowIdentity=True)
    Loops: dict[int, tuple[AsmUse, ...]] = {}
    Faces: set[int] = set()
    for _ in range(FaceCount):
        FaceValue = RequireAsm(Table, FaceId, "face", 10)
        if (
            FaceId in Faces
            or ReadAsmPtr(FaceValue, 5) != ShellId
            or ReadAsmPtr(FaceValue, 6) != -1
            or IsAsmFlag(FaceValue, 9)
        ):
            raise ValueError("Fusion Cut result face is outside its closed shell")
        _ = RequireAsm(Table, ReadAsmPtr(FaceValue, 7), "plane-surface", 11)
        Faces.add(FaceId)
        LoopId = ReadAsmPtr(FaceValue, 4)
        for _ in range(2):
            if LoopId in Loops:
                raise ValueError("Fusion Cut result repeats a boundary loop")
            RingValue = ReadAsmRim(Table, FaceId, LoopId, 4, ResultLoop=True)
            if len(RingValue) != 4:
                raise ValueError("Fusion Cut result requires four sided boundary loops")
            Loops[LoopId] = RingValue
            LoopValue = RequireAsm(Table, LoopId, "loop", 6)
            LoopId = ReadAsmPtr(LoopValue, 3)
            if LoopId == -1:
                break
        if LoopId != -1:
            raise ValueError("Fusion Cut result face has unexpected additional loops")
        FaceId = ReadAsmPtr(FaceValue, 3)
    if FaceId != -1 or len(Loops) != 12:
        raise ValueError("Fusion Cut result shell face or loop inventory disagrees")
    return Loops
