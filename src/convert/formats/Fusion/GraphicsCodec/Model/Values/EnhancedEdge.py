from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class EnhancedEdge:
    StreamIndex: int
    ByteOffset: int
    Points: tuple[tuple[float, ...], ...]
    Normals: tuple[tuple[float, ...], ...]
