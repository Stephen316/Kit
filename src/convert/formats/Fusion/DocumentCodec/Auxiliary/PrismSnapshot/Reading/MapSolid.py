from convert.formats.Fusion.BrepCodec.Prism.Reading.MapPrismFaces import MapPrismFaces
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismGraph import PrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismRoles import PrismRoles
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstEdge,
    KFirstCurve,
    KFirstVertex,
    KFirstPoint,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def MapSolid(Table: AsmTable, Graph: PrismGraph, Roles: PrismRoles) -> dict[int, int]:
    Mapping = {
        0: 0,
        1: 1,
        2: ReadAsmPtr(RequireAsm(Table, 1, "body", 6), 3),
        3: Graph.ShellId,
    }
    Mapping.update(MapPrismFaces(Table, Graph, Roles))
    for Identity, RoleIndex in Roles.Edges.items():
        Mapping[KFirstEdge + RoleIndex] = Identity
        Mapping[KFirstCurve + RoleIndex] = ReadAsmPtr(
            RequireAsm(Table, Identity, "edge", 11), 8
        )
    for Identity, Corner in Roles.Corners.items():
        Mapping[KFirstVertex + Corner] = Identity
        Mapping[KFirstPoint + Corner] = ReadAsmPtr(
            RequireAsm(Table, Identity, "vertex", 6), 5
        )
    return Mapping
