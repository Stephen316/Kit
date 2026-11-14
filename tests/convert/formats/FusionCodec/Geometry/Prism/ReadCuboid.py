from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import ReadAsmPoints
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import AsmPrism, ReadAsmShell
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import ReadAsmEdges
from convert.formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse, ReadAsmRim
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from convert.formats.Fusion.Topology.AsmEdge.PrismCarriers import CheckPrismLine
from tests.convert.formats.FusionCodec.Geometry.Prism.PrismEvidence import PrismEvidence


def ReadCuboid(DataValue: bytes) -> PrismEvidence:
    Table = ReadAsmTable(DataValue)
    ShellId, FaceId = ReadAsmShell(Table, 1)
    Rings: dict[int, tuple[AsmUse, ...]] = {}
    for _ in range(6):
        FaceValue = RequireAsm(Table, FaceId, "face", 10)
        assert ReadAsmPtr(FaceValue, 5) == ShellId
        assert not IsAsmFlag(FaceValue, 8)
        assert not IsAsmFlag(FaceValue, 9)
        Rings[FaceId] = ReadAsmRim(Table, FaceId, ReadAsmPtr(FaceValue, 4), 4)
        FaceId = ReadAsmPtr(FaceValue, 3)
    assert FaceId == -1 and len(Rings) == 6
    Prism = AsmPrism({}, Rings)
    Edges = ReadAsmEdges(Table, Prism, 4)
    Points = ReadAsmPoints(Table, Edges, 4)
    for EdgeValue in Edges.values():
        CheckPrismLine(Table, EdgeValue, Points)
    return PrismEvidence(Table, Prism, Edges, Points)
