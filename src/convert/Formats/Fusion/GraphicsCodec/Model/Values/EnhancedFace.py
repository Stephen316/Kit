from dataclasses import dataclass as MakeDataClass


# enhanced face needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class EnhancedFace:
    StreamIndex: int
    ByteOffset: int
    Points: tuple[tuple[float, ...], ...]
    Normals: tuple[tuple[float, ...], ...]
    Coords: tuple[tuple[float, ...], ...]
    Indices: tuple[int, ...]
    EdgeIds: tuple[int, ...]
