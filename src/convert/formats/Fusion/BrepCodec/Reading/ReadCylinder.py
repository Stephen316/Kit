from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmNum,
    ReadAsmVec,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadCylinder(
    Table: AsmTable, Mapping: dict[int, int], HasHistory: bool
) -> CylinderBody:
    Offset = 0 if HasHistory else 2
    Surface = RequireAsm(Table, Mapping[17 + Offset], "cone-surface", 17)
    TopCurve = RequireAsm(Table, Mapping[22 + Offset], "ellipse-curve", 9)
    BottomCurve = RequireAsm(Table, Mapping[23 + Offset], "ellipse-curve", 9)
    TopCenter = ReadAsmVec(TopCurve, 3, 19)
    BaseCenter = ReadAsmVec(BottomCurve, 3, 19)
    BasePoint = (BaseCenter.x * 10, BaseCenter.y * 10, BaseCenter.z * 10)
    return CylinderBody(
        ReadAsmNum(Surface, 11) * 10, TopCenter.z * 10 - BasePoint[2], BasePoint
    )
