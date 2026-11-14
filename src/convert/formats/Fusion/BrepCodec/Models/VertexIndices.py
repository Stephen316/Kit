from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class VertexIndices:
    TopIndex: int = 0
    BottomIndex: int = 0

    def __post_init__(self) -> None:
        for IndexValue in (self.TopIndex, self.BottomIndex):
            if type(IndexValue) is not int or IndexValue not in (0, 2):
                raise ValueError("Unsupported Fusion BRep vertex edge index")
