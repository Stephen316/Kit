from typing import TypedDict


# the tsm case boundary needs grouped coverage so repository automation cannot silently change its observable contract
class TsmCase(TypedDict):
    Name: str
    Source: str
    SourceHash: str
    SemanticHash: str
    Faces: int
    Vertices: int
    Grips: int
