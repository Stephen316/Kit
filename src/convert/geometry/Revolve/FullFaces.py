from convert.geometry.Revolve.SweepSides import BuildSide
from interchange.brep.surfaces.BrepSurfaces import BrepSurface, PlaneSurface
from interchange.brep.topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)
from interchange.geometry.models.Transform import Transform


# periodic faces share the orbits on either side without adding angular caps
def BuildFullFaces(
    Prefix: str,
    Meridian: tuple[tuple[float, float], ...],
    Frame: Transform,
    Edges: dict[int, BrepEdge],
) -> tuple[
    tuple[BrepSurface, ...],
    tuple[BrepFace, ...],
    tuple[BrepLoop, ...],
    tuple[BrepCoedge, ...],
]:
    Surfaces: list[BrepSurface] = []
    Faces: list[BrepFace] = []
    Loops: list[BrepLoop] = []
    Coedges: list[BrepCoedge] = []
    for Index, First in enumerate(Meridian):
        Following = (Index + 1) % len(Meridian)
        Second = Meridian[Following]
        if First[0] == Second[0] == 0.0:
            continue
        SideId = f"{Prefix}-side-{Index}"
        Surface, SameSense = BuildSide(f"{SideId}-surface", First, Second, Frame)
        Rings = (
            (Edges.get(Index), False, First[0]),
            (Edges.get(Following), True, Second[0]),
        )
        if isinstance(Surface, PlaneSurface):
            Rings = Rings[::-1] if First[0] < Second[0] else Rings
        elif First[0] == 0.0:
            Rings = Rings[::-1]
        FaceLoops: list[str] = []
        for EdgeValue, Reversed, Radius in Rings:
            if EdgeValue is None or (
                Radius == 0.0 and isinstance(Surface, PlaneSurface)
            ):
                continue
            LoopId = f"{SideId}-loop-{len(FaceLoops)}"
            UseValue = BrepCoedge(f"{LoopId}-use", EdgeValue.id, reversed=Reversed)
            Loops.append(BrepLoop(LoopId, (UseValue.id,), outer=not FaceLoops))
            Coedges.append(UseValue)
            FaceLoops.append(LoopId)
        Surfaces.append(Surface)
        Faces.append(
            BrepFace(
                f"{SideId}-face", Surface.id, tuple(FaceLoops), same_sense=SameSense
            )
        )
    return tuple(Surfaces), tuple(Faces), tuple(Loops), tuple(Coedges)
