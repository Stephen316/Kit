from dataclasses import dataclass as MakeDataClass


# enhanced edge needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class EnhancedEdge:
    StreamIndex: int
    ByteOffset: int
    Points: tuple[tuple[float, ...], ...]
    Normals: tuple[tuple[float, ...], ...]
