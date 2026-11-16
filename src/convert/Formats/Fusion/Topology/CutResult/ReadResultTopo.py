from collections import Counter

from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.Formats.Fusion.Topology.AsmEdge.AsmPoints import ReadAsmVerts
from convert.Formats.Fusion.Topology.AsmEdge.AsmPrismEdges import (
    AsmPrismEdge,
    ReadRingEdges,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.Formats.Fusion.Topology.AsmEdge.PrismCarriers import CheckPrismLine
from convert.Formats.Fusion.Topology.CutResult.CheckResultRim import CheckResultRim
from convert.Formats.Fusion.Topology.CutResult.CutMass import (
    CutResultStats,
    ReadCutMass,
)
from convert.Formats.Fusion.Topology.CutResult.ReadResultRims import ReadResultRims
from convert.Formats.Fusion.Topology.CutResult.ResultBounds import ResultBounds
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Records.RecordTopology import TopologyCounts


# disconnected face graphs cannot present one current solid merely through a shared shell record
def CheckResultJoin(Edges: dict[int, AsmPrismEdge]) -> None:
    Adjacent: dict[int, set[int]] = {}
    for EdgeValue in Edges.values():
        First, Second = EdgeValue.Faces
        Adjacent.setdefault(First, set()).add(Second)
        Adjacent.setdefault(Second, set()).add(First)
    SeenFaces: set[int] = set()
    Pending = [next(iter(Adjacent))]
    while Pending:
        Identity = Pending.pop()
        if Identity not in SeenFaces:
            SeenFaces.add(Identity)
            Pending.extend(Adjacent[Identity] - SeenFaces)
    if SeenFaces != set(Adjacent):
        raise ValueError("Fusion Cut result shell is disconnected")


# coordinate bounds rely on complete one to one carrier ownership
def CheckResultRefs(
    Table: AsmTable,
    Loops: dict[int, tuple[AsmUse, ...]],
    EdgeIds: tuple[int, ...],
    VertexIds: tuple[int, ...],
    FaceCount: int,
) -> None:
    Faces = {Value[0].FaceId for Value in Loops.values()}
    Carriers = (
        (Faces, "face", 10, 7, FaceCount),
        (EdgeIds, "edge", 11, 8, len(EdgeIds)),
        (VertexIds, "vertex", 6, 5, len(VertexIds)),
    )
    for Identities, KindValue, Width, Field, Count in Carriers:
        References = {
            ReadAsmPtr(RequireAsm(Table, Identity, KindValue, Width), Field)
            for Identity in Identities
        }
        if len(References) != Count:
            raise ValueError("Fusion Cut result shares or omits an analytic carrier")


# exact loop structures and carriers establish saved counts and bounds for the supported cut extent
def ReadResultTopo(
    Table: AsmTable, BodyIndex: int, FaceCount: int, Definition: ExtrudeFeature
) -> CutResultStats:
    Loops = ReadResultRims(Table, BodyIndex, FaceCount)
    Edges = ReadRingEdges(Table, tuple(Loops.values()), 24)
    Points = ReadAsmVerts(Table, Edges, 16)
    Counts = Counter(Value.Name for Value in Table.Records)
    Expected = {
        "body": 1,
        "lump": 1,
        "shell": 1,
        "face": FaceCount,
        "loop": len(Loops),
        "coedge": 48,
        "edge": len(Edges),
        "vertex": len(Points),
        "point": len(Points),
        "plane-surface": FaceCount,
        "straight-curve": len(Edges),
    }
    if any(Counts[KindValue] != Number for KindValue, Number in Expected.items()):
        raise ValueError("Fusion Cut result contains unowned topology or carriers")
    CheckResultRefs(Table, Loops, tuple(Edges), tuple(Points), FaceCount)
    CheckResultJoin(Edges)
    for Value in Edges.values():
        CheckPrismLine(Table, Value, Points)
    Normals = {
        RingValue[0].FaceId: CheckResultRim(Table, RingValue, Edges, Points)
        for RingValue in Loops.values()
    }
    Topology = TopologyCounts(
        solid_count=1,
        shell_count=1,
        face_count=FaceCount,
        edge_count=len(Edges),
        vertex_count=len(Points),
        bounding_box=ResultBounds(Points),
    )
    return ReadCutMass(
        Table, tuple(Loops.values()), Edges, Points, Normals, Topology, Definition
    )
