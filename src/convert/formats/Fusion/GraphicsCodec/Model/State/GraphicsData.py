from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)


@MakeDataClass(frozen=True, slots=True)
class GraphicsData:
    WorldData: bytes
    MeshStreams: tuple[GraphicsStream, ...]
    FusionStreams: tuple[GraphicsStream, ...]
