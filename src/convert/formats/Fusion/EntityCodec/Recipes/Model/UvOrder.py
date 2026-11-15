from dataclasses import dataclass as MakeDataClass


# uv order needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class UvOrder:
    FaceVertexCount: int
    UOrder: int
    ULowerOrder: int
    UUpperOrder: int
    VOrder: int
    VLowerOrder: int
    VUpperOrder: int
