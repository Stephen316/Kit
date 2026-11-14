from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh


@MakeDataClass(frozen=True, slots=True)
class DocumentMesh:
    Name: str
    Mesh: ParaMesh
