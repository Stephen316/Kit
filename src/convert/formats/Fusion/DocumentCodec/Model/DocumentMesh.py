from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh


# document mesh needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class DocumentMesh:
    Name: str
    Mesh: ParaMesh
