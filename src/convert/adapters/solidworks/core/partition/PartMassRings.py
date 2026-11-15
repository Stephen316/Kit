from collections import Counter
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepCoedge, BrepEdge, BrepFace, BrepLoop
from interchange.geometry.models.VectorSpace import SpaceVector


# each face ring resolves its own vertices and directed edge occurrences
@Dataclass(frozen=True, slots=True)
class MassRingMap:
    Points: dict[str, SpaceVector]
    Edges: dict[str, BrepEdge]
    Coedges: dict[str, BrepCoedge]
    Loops: dict[str, BrepLoop]
    Faces: dict[str, BrepFace]


# the saved planar result must contain one complete solid shell
def CheckMassShell(ModelValue: BrepModel) -> None:
    RequireArch(
        (len(ModelValue.regions), len(ModelValue.shells), len(ModelValue.shell_uses)),
        (1, 1, 1), "one region and shell for the saved planar result",
    )
    (Region,), (Shell,), (ShellUse,) = (
        ModelValue.regions, ModelValue.shells, ModelValue.shell_uses
    )
    RequireArch(
        (Region.solid, Shell.closed, Region.shell_use_ids, ShellUse.shell_id),
        (True, True, (ShellUse.id,), Shell.id), "active region owns a complete solid shell",
    )
    FaceUses = {Value.id for Value in ModelValue.face_uses}
    RequireArch(set(Shell.face_use_ids), FaceUses, "shell owns all face uses")
    RequireArch(
        len(Shell.face_use_ids), len(ModelValue.faces),
        "one shell use for each saved face",
    )
    RequireArch(
        {Value.face_id for Value in ModelValue.face_uses},
        {Value.id for Value in ModelValue.faces},
        "every face belongs to the active solid shell",
    )


# connected coedges must visit successive unique vertices and return to the first
def ReadMassRingMut(
    Source: MassRingMap, LoopId: str, Reverse: bool,
    Incidence: Counter[tuple[str, bool]],
) -> tuple[SpaceVector, ...]:
    CoedgeUses = tuple(Source.Coedges[Value] for Value in Source.Loops[LoopId].coedge_ids)
    Incidence.update((Value.edge_id, Value.reversed != Reverse) for Value in CoedgeUses)
    Ordered = tuple(
        (
            (Source.Edges[Value.edge_id].end_vertex_id, Source.Edges[Value.edge_id].start_vertex_id)
            if Value.reversed
            else (Source.Edges[Value.edge_id].start_vertex_id, Source.Edges[Value.edge_id].end_vertex_id)
        )
        for Value in CoedgeUses
    )
    Starts = tuple(First for First, _ in Ordered)
    RequireArch(len(set(Starts)) == len(Starts) >= 3, True, "distinct saved loop vertices")
    RequireArch(
        tuple(Second for _, Second in Ordered), Starts[1:] + Starts[:1],
        "closed oriented coedge loop",
    )
    return tuple(Source.Points[Vertex] for Vertex in (Starts[::-1] if Reverse else Starts))


# the active planar shell must account for all saved loops and opposite edge uses
def ReadMassRings(ModelValue: BrepModel) -> tuple[tuple[SpaceVector, ...], ...]:
    CheckMassShell(ModelValue)
    Source = MassRingMap(
        {Value.id: Value.point for Value in ModelValue.vertices},
        {Value.id: Value for Value in ModelValue.edges},
        {Value.id: Value for Value in ModelValue.coedges},
        {Value.id: Value for Value in ModelValue.loops},
        {Value.id: Value for Value in ModelValue.faces},
    )
    ShellReverse = ModelValue.shell_uses[0].reversed
    Incidence: Counter[tuple[str, bool]] = Counter()
    LoopIds = tuple(LoopId for FaceValue in ModelValue.faces for LoopId in FaceValue.loop_ids)
    RequireArch(Counter(LoopIds), Counter(Source.Loops.keys()), "one face owns each saved loop")
    Rings = tuple(
        ReadMassRingMut(Source, LoopId, UseValue.reversed != ShellReverse, Incidence)
        for UseValue in ModelValue.face_uses
        for LoopId in Source.Faces[UseValue.face_id].loop_ids
    )
    RequireArch(
        Incidence, Counter((EdgeId, Direction) for EdgeId in Source.Edges for Direction in (False, True)),
        "opposite shell uses for each saved edge",
    )
    return Rings
