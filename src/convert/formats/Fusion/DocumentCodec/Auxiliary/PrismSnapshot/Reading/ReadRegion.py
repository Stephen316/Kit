from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismLine import ReadPrismLine
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismPlane import ReadPrismPlane
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismVec import ReadPrismVec
from convert.formats.Fusion.BrepCodec.Reading.ReadSketchLink import ReadSketchLink
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionEdge import (
    RegionEdge,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmNum,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadRegion(
    Table: AsmTable, Mapping: dict[int, int], Start: int, AttrStart: int
) -> RegionFrame:
    Corners = tuple(
        ReadPrismVec(RequireAsm(Table, Mapping[Start + 21 + Index], "point", 4), 3, 19)
        for Index in range(4)
    )
    Edges = tuple(
        RequireAsm(Table, Mapping[Start + 9 + Index], "edge", 11) for Index in range(4)
    )
    EdgeIds = tuple(Mapping[Start + 9 + Index] for Index in range(4))
    Owners = tuple(
        EdgeIds.index(
            ReadAsmPtr(RequireAsm(Table, Mapping[Start + 13 + Index], "vertex", 6), 3)
        )
        for Index in range(4)
    )
    return RegionFrame(
        Corners,
        tuple(
            RegionEdge(
                ReadAsmNum(EdgeValue, 4),
                ReadAsmNum(EdgeValue, 6),
                ReadPrismLine(Table, ReadAsmPtr(EdgeValue, 8)),
            )
            for EdgeValue in Edges
        ),
        Owners,
        ReadPrismPlane(Table, Mapping[Start + 4]),
        tuple(ReadSketchLink(Table, Mapping[AttrStart + Index]) for Index in range(4)),
        tuple(
            ReadSketchLink(Table, Mapping[AttrStart + 4 + Index]) for Index in range(4)
        ),
    )
