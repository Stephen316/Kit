from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import KPrismRecords
from convert.formats.Fusion.BrepCodec.Prism.Reading.MapPrismAttrs import MapPrismAttrs
from convert.formats.Fusion.BrepCodec.Prism.Reading.MapPrismFaces import MapPrismFaces
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismGraph import PrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismRoles import PrismRoles
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstCurve,
    KFirstEdge,
    KFirstPoint,
    KFirstVertex,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def MapPrism(Table: AsmTable, Graph: PrismGraph, Roles: PrismRoles) -> dict[int, int]:
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
    Mapping.update(MapPrismAttrs(Table, Mapping))
    if set(Mapping) != set(range(KPrismRecords)) or set(Mapping.values()) != set(
        range(KPrismRecords)
    ):
        raise ValueError("Unsupported prism record inventory or aliases")
    return Mapping
