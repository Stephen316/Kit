from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from typing import cast as CastValue
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload


def SceneTargets(Value: GraphicScene, ActSegment: int) -> tuple[EntityRef, ...]:
    Pending: list[object] = [Value]
    Results: set[EntityRef] = set()
    while Pending:
        Current = Pending.pop()
        if isinstance(Current, EntityRef):
            Results.add(Current)
        elif isinstance(Current, tuple):
            Pending.extend(CastValue(tuple[object, ...], Current))
        elif IsDataClass(Current) and not isinstance(Current, type):
            Pending.extend(
                CastValue(object, getattr(Current, Entry.name))
                for Entry in DataFields(Current)
            )
            if isinstance(Current, NodePayload) and Current.ActEntity is not None:
                Results.add(EntityRef(ActSegment, Current.ActEntity))
    return tuple(sorted(Results, key=lambda Entry: (Entry.SegmentId, Entry.ObjectId)))
