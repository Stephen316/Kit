from typing import TypedDict


class MeshCase(TypedDict):
    Archive: str
    Member: str
    SourceHash: str
    PayloadHash: str
    SemanticHash: str
    Vertices: int
    Triangles: int
