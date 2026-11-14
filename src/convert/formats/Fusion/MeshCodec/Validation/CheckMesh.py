from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh
from convert.formats.Fusion.MeshCodec.Validation.CheckEdges import CheckEdges
from convert.formats.Fusion.MeshCodec.Validation.CheckGeometry import CheckGeometry
from convert.formats.Fusion.MeshCodec.Validation.CheckNormals import CheckNormals
from convert.formats.Fusion.MeshCodec.Validation.CheckRegistry import CheckRegistry


def CheckMesh(Value: ParaMesh) -> None:
    CheckRegistry(Value.Registry)
    CheckGeometry(Value)
    CheckNormals(Value)
    CheckEdges(Value)
    KeyValues = {Group.GroupKey for Group in Value.Registry.Groups}
    if len(Value.FaceGroups) != len(Value.Corners) // 3:
        raise ValueError("Fusion mesh face-group allocation differs from triangles")
    if any(
        type(KeyValue) is not int or KeyValue not in KeyValues
        for KeyValue in Value.FaceGroups
    ):
        raise ValueError("Fusion mesh triangle references an undeclared face group")
    SizeValue = len(Value.Positions) * 12 + len(Value.Corners) * 4
    SizeValue += len(Value.Normals) * 8 + len(Value.Overrides) * 4
    SizeValue += len(Value.Edges) * 8 + len(Value.FaceGroups) * 4
    if SizeValue > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh total decoded allocation exceeds limit")
