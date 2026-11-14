from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class EnhancedFace:
    StreamIndex: int
    ByteOffset: int
    Points: tuple[tuple[float, ...], ...]
    Normals: tuple[tuple[float, ...], ...]
    Coords: tuple[tuple[float, ...], ...]
    Indices: tuple[int, ...]
    EdgeIds: tuple[int, ...]
