from dataclasses import dataclass as MakeDataClass


# stored boundary identities remain distinct from the view table and neutral model identifiers
@MakeDataClass(frozen=True, slots=True)
class AsmFaceHit:
    FaceIndex: int
    LoopIndex: int
    PlaneIndex: int
    EdgeIndices: tuple[int, ...]
    VertexIndices: tuple[int, ...]
