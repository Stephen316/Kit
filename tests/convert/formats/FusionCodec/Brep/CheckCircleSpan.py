from math import pi as KCircleHalf

from pytest import approx as Approx

from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmNum
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmVec
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def CheckCircleSpan(Table: AsmTable, Model: CylinderBody, CurveCount: int) -> None:
    Curves = tuple(Record for Record in Table.Records if Record.Name == "ellipse-curve")
    assert len(Curves) == CurveCount
    Centers = tuple(ReadAsmVec(Record, 3, 19) for Record in Curves)
    RadiusVectors = tuple(ReadAsmVec(Record, 5, 20) for Record in Curves)
    assert all(Vector.x == Approx(Model.Radius / 10) for Vector in RadiusVectors)
    assert all(Vector.y == Vector.z == 0 for Vector in RadiusVectors)
    assert all(
        Center.x == Approx(Model.BasePoint[0] / 10)
        and Center.y == Approx(Model.BasePoint[1] / 10)
        for Center in Centers
    )
    Heights = sorted(Center.z for Center in Centers)
    assert Heights == Approx(
        [Model.BasePoint[2] / 10] * (CurveCount - 1)
        + [(Model.BasePoint[2] + Model.Height) / 10]
    )
    SpanHeight = Heights[-1] - Heights[0]
    assert SpanHeight == Approx(Model.Height / 10)
    assert KCircleHalf * RadiusVectors[0].x ** 2 * SpanHeight == Approx(
        KCircleHalf * Model.Radius**2 * Model.Height / 1000
    )
    Surface = next(Record for Record in Table.Records if Record.Name == "cone-surface")
    assert ReadAsmNum(Surface, 11) == Approx(Model.Radius / 10)
    for Plane in (Record for Record in Table.Records if Record.Name == "plane-surface"):
        Reference = ReadAsmVec(Plane, 5, 20)
        assert (Reference.x, Reference.y, Reference.z) == (1, 0, 0)
