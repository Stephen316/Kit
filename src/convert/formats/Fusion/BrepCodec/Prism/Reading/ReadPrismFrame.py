from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismGraph import PrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismRoles import PrismRoles
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismEdge import ReadPrismEdge
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismPlane import ReadPrismPlane
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstEdge,
    KFirstFace,
    KFirstPlane,
    KFirstVertex,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadPrismFrame(
    Table: AsmTable, Graph: PrismGraph, Roles: PrismRoles, Mapping: dict[int, int]
) -> PrismFrame:
    FaceIds = tuple(Mapping[KFirstFace + Index] for Index in range(6))
    Starts = tuple(Graph.Rings[Identity][0] for Identity in FaceIds)
    FaceStarts = tuple(
        Roles.Corners[Graph.Edges[Value.EdgeId].Vertices[int(Value.Reverse)]]
        for Value in Starts
    )
    return PrismFrame(
        tuple(Graph.Points[Mapping[KFirstVertex + Index]] for Index in range(8)),
        tuple(Roles.Faces[Identity] for Identity in Graph.Faces),
        FaceStarts,
        tuple(
            IsAsmFlag(RequireAsm(Table, Identity, "face", 10), 8)
            for Identity in FaceIds
        ),
        tuple(
            ReadPrismEdge(Table, Mapping[KFirstEdge + Index], Roles)
            for Index in range(12)
        ),
        tuple(
            Roles.Edges[
                ReadAsmPtr(
                    RequireAsm(Table, Mapping[KFirstVertex + Index], "vertex", 6), 3
                )
            ]
            for Index in range(8)
        ),
        tuple(
            ReadPrismPlane(Table, Mapping[KFirstPlane + Index]) for Index in range(6)
        ),
    )
