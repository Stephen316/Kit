from collections.abc import Iterable
from dataclasses import replace as Replace
from typing import TypeVar

from interchange.brep.Curves.BrepCurves import BrepEntity
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepBody, BrepRegion

# topology references preserve the type of their owning record table
KEntityType = TypeVar("KEntityType", bound=BrepEntity)


# region closure follows typed references while preserving first occurrence order
def TakeEntities(
    Records: tuple[KEntityType, ...], IdValues: Iterable[str]
) -> tuple[KEntityType, ...]:
    Lookup = {Value.EntityId: Value for Value in Records}
    return tuple(Lookup[IdValue] for IdValue in dict.fromkeys(IdValues) if IdValue)


# each region measurement uses only topology and geometry reached from one shell
def ExtractRegion(
    ModelValue: BrepModel, Region: BrepRegion, Carrier: BrepBody
) -> BrepModel:
    ShellUses = TakeEntities(ModelValue.shell_uses, Region.shell_use_ids)
    Shells = TakeEntities(ModelValue.shells, (Value.shell_id for Value in ShellUses))
    FaceUses = TakeEntities(
        ModelValue.face_uses,
        (RefId for Value in Shells for RefId in Value.face_use_ids),
    )
    Faces = TakeEntities(ModelValue.faces, (Value.face_id for Value in FaceUses))
    LoopValues = TakeEntities(
        ModelValue.loops, (RefId for Value in Faces for RefId in Value.loop_ids)
    )
    Coedges = TakeEntities(
        ModelValue.coedges,
        (RefId for Value in LoopValues for RefId in Value.coedge_ids),
    )
    EdgeValues = TakeEntities(ModelValue.edges, (Value.edge_id for Value in Coedges))
    Vertices = TakeEntities(
        ModelValue.vertices,
        (
            RefId
            for Value in EdgeValues
            for RefId in (Value.start_vertex_id, Value.end_vertex_id)
        ),
    )
    return Replace(
        ModelValue,
        regions=(Region,),
        bodies=(Replace(Carrier, region_ids=(Region.id,)),),
        shell_uses=ShellUses,
        shells=Shells,
        face_uses=FaceUses,
        faces=Faces,
        loops=LoopValues,
        coedges=Coedges,
        edges=EdgeValues,
        vertices=Vertices,
        curves=TakeEntities(
            ModelValue.curves, (Value.curve_id for Value in EdgeValues)
        ),
        pcurves=TakeEntities(
            ModelValue.pcurves, (Value.pcurve_id for Value in Coedges)
        ),
        surfaces=TakeEntities(
            ModelValue.surfaces, (Value.surface_id for Value in Faces)
        ),
    )
