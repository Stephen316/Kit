from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)


# graphics data needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class GraphicsData:
    WorldData: bytes
    MeshStreams: tuple[GraphicsStream, ...]
    FusionStreams: tuple[GraphicsStream, ...]
