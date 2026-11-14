from convert.formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame
from convert.formats.Fusion.BrepCodec.Frustum.Reading.ReadFrameVec import ReadFrameVec
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmInt,
    ReadAsmNum,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadRimFrame(Table: AsmTable, Mapping: dict[int, int], IsUpper: bool) -> RimFrame:
    Offset = 0 if IsUpper else 1
    Curve = RequireAsm(Table, Mapping[22 + Offset], "ellipse-curve", 9)
    Plane = RequireAsm(Table, Mapping[18 + Offset], "plane-surface", 11)
    Point = RequireAsm(Table, Mapping[24 + Offset], "point", 4)
    Vertex = RequireAsm(Table, Mapping[20 + Offset], "vertex", 6)
    Owner = RequireAsm(Table, Mapping[15 + Offset], "edge", 11)
    SideUse = RequireAsm(Table, Mapping[11 + Offset], "coedge", 11)
    CapUse = RequireAsm(Table, Mapping[13 + Offset], "coedge", 11)
    return RimFrame(
        ReadFrameVec(Curve, 3, 19),
        ReadFrameVec(Curve, 4, 20),
        ReadFrameVec(Curve, 5, 20),
        ReadAsmNum(Curve, 6),
        ReadFrameVec(Point, 3, 19),
        ReadFrameVec(Plane, 3, 19),
        ReadFrameVec(Plane, 4, 20),
        ReadFrameVec(Plane, 5, 20),
        IsAsmFlag(Plane, 6),
        ReadAsmNum(Owner, 4),
        ReadAsmNum(Owner, 6),
        IsAsmFlag(Owner, 9),
        IsAsmFlag(SideUse, 7),
        IsAsmFlag(CapUse, 7),
        ReadAsmInt(Vertex, 4),
    )
