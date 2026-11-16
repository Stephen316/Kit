from collections.abc import Mapping

from convert.Formats.Fusion.Topology.BodyEvidence import (
    GetBodyEvidence,
    LinkBodyRecords,
)
from convert.Formats.Fusion.Topology.NativeBody import NativeBody
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureBody import DesignBody


# only reconciled native members may receive typed body identifiers and geometry
def GetSolidMembers(
    ComponentId: int,
    Members: tuple[NativeBody, ...],
    Bodies: tuple[DesignBody, ...],
    Model: BrepModel,
) -> tuple[tuple[DesignBody, ...], Mapping[str, object]]:
    if not Bodies or any(Value.ComponentId != ComponentId for Value in Members):
        raise ValueError(f"Fusion component {ComponentId} has invalid solid membership")
    LinkedBodies, LinkedIds = LinkBodyRecords(Bodies, Members)
    BodyIds = {Value.id for Value in LinkedBodies}
    ModelIds = tuple(Value.design_body_id for Value in Model.bodies)
    if (
        len(LinkedIds) != len(LinkedBodies)
        or set(LinkedIds.values()) != BodyIds
        or len(BodyIds) != len(LinkedBodies)
        or len(ModelIds) != len(LinkedBodies)
        or set(ModelIds) != BodyIds
    ):
        raise ValueError(
            f"Fusion component {ComponentId} body and B-rep links disagree"
        )
    return LinkedBodies, GetBodyEvidence(ComponentId, Members, LinkedIds)
