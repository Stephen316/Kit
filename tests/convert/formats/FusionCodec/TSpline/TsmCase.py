from typing import TypedDict


class TsmCase(TypedDict):
    Name: str
    Source: str
    SourceHash: str
    SemanticHash: str
    Faces: int
    Vertices: int
    Grips: int
