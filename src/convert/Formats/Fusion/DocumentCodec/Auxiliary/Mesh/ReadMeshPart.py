from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshName import MeshName
from convert.Formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.Formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh


# the mesh part operation needs a distinct decoding boundary so supporting records retain their owning document relationships
def ReadMeshPart(Value: ContainerPart) -> DocumentMesh:
    _ = MeshName(Value.Name)
    return DocumentMesh(Value.Name, ReadParaMesh(Value.Payload))
