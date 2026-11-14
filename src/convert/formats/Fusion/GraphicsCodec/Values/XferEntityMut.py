from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferEntityMut(
    State: SceneCodec, Status: int | None, Target: EntityRef | None
) -> tuple[int, EntityRef | None]:
    EntityStatus = State.Integer(Status, "<i")
    EntityLink = None
    if EntityStatus in (1, 2):
        SegmentId = State.Integer(Target.SegmentId if Target else None)
        ObjectId = State.Integer(Target.ObjectId if Target else None, ">Q")
        EntityLink = EntityRef(SegmentId, ObjectId)
    elif EntityStatus != 0:
        raise ValueError("Unsupported graphics entity status")
    return EntityStatus, EntityLink
