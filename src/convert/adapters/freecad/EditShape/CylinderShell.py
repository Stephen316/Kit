from dataclasses import dataclass as MakeDataClass

from interchange.brep.surfaces.BrepSurfaces import BrepSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepCoedge

# saved geometry must retain kernel sized tolerances around its analytic edges
KMaxShapeTolerance = 1e-6


# shell orientation and loop traversals are needed together to prove material side
@MakeDataClass(frozen=True, slots=True)
class CylinderFace:
    Surface: BrepSurface
    Coedges: tuple[BrepCoedge, ...]
    Reversed: bool


# a single closed shell is the only topology a standalone cylinder can contribute
def HasCylShell(Model: BrepModel) -> bool:
    if (
        len(Model.bodies) != 1
        or len(Model.regions) != 1
        or len(Model.shell_uses) != 1
        or len(Model.shells) != 1
        or len(Model.faces) != 3
        or len(Model.face_uses) != 3
        or len(Model.surfaces) != 3
        or len(Model.loops) != 3
        or len(Model.coedges) != 6
        or len(Model.edges) != 3
        or len(Model.curves) != 3
        or len(Model.vertices) != 2
        or Model.wires
    ):
        return False
    BodyValue = Model.bodies[0]
    RegionValue = Model.regions[0]
    ShellUse = Model.shell_uses[0]
    ShellValue = Model.shells[0]
    return (
        not BodyValue.wire_ids
        and not BodyValue.vertex_ids
        and BodyValue.region_ids == (RegionValue.id,)
        and RegionValue.solid
        and RegionValue.shell_use_ids == (ShellUse.id,)
        and ShellUse.shell_id == ShellValue.id
        and ShellValue.closed
        and set(ShellValue.face_use_ids) == {Value.id for Value in Model.face_uses}
        and {Value.face_id for Value in Model.face_uses}
        == {Value.id for Value in Model.faces}
        and all(
            0.0 <= Value.tolerance <= KMaxShapeTolerance
            for Value in (*Model.vertices, *Model.edges, *Model.faces)
        )
    )


# one outer wire per face prevents holes and extra topology from matching a cylinder
def ReadCylFaces(Model: BrepModel) -> tuple[CylinderFace, ...]:
    FaceUses = {Value.face_id: Value for Value in Model.face_uses}
    Surfaces = {Value.id: Value for Value in Model.surfaces}
    Loops = {Value.id: Value for Value in Model.loops}
    Coedges = {Value.id: Value for Value in Model.coedges}
    if any(len(Value.loop_ids) != 1 for Value in Model.faces):
        return ()
    if {Value.loop_ids[0] for Value in Model.faces} != set(Loops):
        return ()
    if {Value.surface_id for Value in Model.faces} != set(Surfaces):
        return ()
    if any(not Value.outer for Value in Loops.values()):
        return ()
    SeenCoedges = tuple(
        CoedgeId for Value in Loops.values() for CoedgeId in Value.coedge_ids
    )
    if len(SeenCoedges) != len(Coedges) or set(SeenCoedges) != set(Coedges):
        return ()
    return tuple(
        CylinderFace(
            Surfaces[Value.surface_id],
            tuple(
                Coedges[KeyValue] for KeyValue in Loops[Value.loop_ids[0]].coedge_ids
            ),
            FaceUses[Value.id].reversed
            ^ Model.shell_uses[0].reversed
            ^ (not Value.same_sense),
        )
        for Value in Model.faces
    )
