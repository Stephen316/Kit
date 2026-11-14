from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class UvOrder:
    FaceVertexCount: int
    UOrder: int
    ULowerOrder: int
    UUpperOrder: int
    VOrder: int
    VLowerOrder: int
    VUpperOrder: int
