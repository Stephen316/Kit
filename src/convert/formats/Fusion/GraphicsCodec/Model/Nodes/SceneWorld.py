from convert.formats.Fusion.GraphicsCodec.Model.Nodes.PrimitiveLod import PrimitiveLod
from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


@MakeDataClass(frozen=True, slots=True)
class SceneWorld:
    WorldKind: str
    RevisionId: int
    PublishMode: int
    Nodes: tuple[ObjectRef | PrimitiveLod, ...]
    Accelerate: bool | None
