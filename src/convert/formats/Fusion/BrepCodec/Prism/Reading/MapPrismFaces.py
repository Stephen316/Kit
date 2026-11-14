from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismGraph import PrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismRoles import PrismRoles
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFaceCorners,
    KFirstCoedge,
    KFirstFace,
    KFirstLoop,
    KFirstPlane,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def MapPrismFaces(
    Table: AsmTable, Graph: PrismGraph, Roles: PrismRoles
) -> dict[int, int]:
    Mapping: dict[int, int] = {}
    for Identity, RoleIndex in Roles.Faces.items():
        FaceValue = RequireAsm(Table, Identity, "face", 10)
        Mapping[KFirstFace + RoleIndex] = Identity
        Mapping[KFirstLoop + RoleIndex] = ReadAsmPtr(FaceValue, 4)
        Mapping[KFirstPlane + RoleIndex] = ReadAsmPtr(FaceValue, 7)
        for UseValue in Graph.Rings[Identity]:
            Vertex = Graph.Edges[UseValue.EdgeId].Vertices[int(UseValue.Reverse)]
            Corner = Roles.Corners[Vertex]
            Mapping[
                KFirstCoedge + 4 * RoleIndex + KFaceCorners[RoleIndex].index(Corner)
            ] = UseValue.Identity
    return Mapping
