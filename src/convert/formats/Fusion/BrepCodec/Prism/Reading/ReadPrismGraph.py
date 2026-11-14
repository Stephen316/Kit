from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismGraph import PrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismRim import ReadPrismRim
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismVec import ReadPrismVec
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import ReadAsmPoints
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import AsmPrism, ReadAsmShell
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import ReadAsmEdges
from convert.formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadPrismGraph(Table: AsmTable) -> PrismGraph:
    ShellId, Current = ReadAsmShell(Table, 1)
    Faces: list[int] = []
    Rings: dict[int, tuple[AsmUse, ...]] = {}
    for _ in range(6):
        FaceValue = RequireAsm(Table, Current, "face", 10)
        if Current in Rings or ReadAsmPtr(FaceValue, 5) != ShellId:
            raise ValueError("Invalid prism face chain")
        Faces.append(Current)
        Rings[Current] = ReadPrismRim(Table, Current, ReadAsmPtr(FaceValue, 4))
        Current = ReadAsmPtr(FaceValue, 3)
    if Current != -1:
        raise ValueError("Prism shell must have exactly six faces")
    Edges = ReadAsmEdges(Table, AsmPrism({}, Rings), 4)
    Vertices = ReadAsmPoints(Table, Edges, 4)
    Points = {
        Identity: ReadPrismVec(
            RequireAsm(
                Table,
                ReadAsmPtr(RequireAsm(Table, Identity, "vertex", 6), 5),
                "point",
                4,
            ),
            3,
            19,
        )
        for Identity in Vertices
    }
    return PrismGraph(ShellId, tuple(Faces), Rings, Edges, Points)
