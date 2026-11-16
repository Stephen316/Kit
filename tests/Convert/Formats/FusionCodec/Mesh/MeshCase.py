from typing import TypedDict


# the mesh case boundary needs grouped coverage so repository automation cannot silently change its observable contract
class MeshCase(TypedDict):
    Archive: str
    Member: str
    SourceHash: str
    PayloadHash: str
    SemanticHash: str
    Vertices: int
    Triangles: int
