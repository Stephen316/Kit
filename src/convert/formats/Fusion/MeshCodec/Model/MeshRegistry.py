from dataclasses import dataclass

from convert.formats.Fusion.MeshCodec.Model.FaceGroup import FaceGroup


@dataclass(frozen=True)
class MeshRegistry:
    MeshId: str
    FusionId: str
    NormalId: str
    FaceGroupCount: int
    VertexStream: str
    CornerStream: str
    NormalStream: str
    OverrideStream: str
    EdgeStream: str
    GroupStream: str
    Groups: tuple[FaceGroup, ...]
    StreamOrder: tuple[str, ...]
