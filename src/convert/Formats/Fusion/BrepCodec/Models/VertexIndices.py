from dataclasses import dataclass as MakeDataClass


# vertex indices needs an explicit state contract so topology identity survives native history reconstruction
@MakeDataClass(frozen=True, slots=True)
class VertexIndices:
    TopIndex: int = 0
    BottomIndex: int = 0

    # invalid vertex indices state must fail at construction so boundary representation history never receives an inconsistent contract
    def __post_init__(self) -> None:
        for IndexValue in (self.TopIndex, self.BottomIndex):
            if type(IndexValue) is not int or IndexValue not in (0, 2):
                raise ValueError("Unsupported Fusion BRep vertex edge index")
