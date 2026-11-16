from __future__ import annotations
from typing import TYPE_CHECKING
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef

if TYPE_CHECKING:
    from convert.Formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


# transfer entity needs an explicit validity boundary so display geometry retains its entity and scene relationships
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
