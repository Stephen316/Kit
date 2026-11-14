from convert.formats.Fusion.BrepCodec.Journal.Complex.ComplexEntity import (
    KComplexEntity,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import (
    IntcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeIntcurve import (
    MakeIntcurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakePcurveNode import (
    MakePcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeSplineNode import (
    MakeSplineNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Writing.MakeTolerant import (
    MakeTcoedgeNode,
    MakeTedgeNode,
    MakeTvertexNode,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeComplex(Value: KComplexEntity) -> AsmRecord:
    if isinstance(Value, SplineNode):
        return MakeSplineNode(Value)
    if isinstance(Value, IntcurveNode):
        return MakeIntcurve(Value)
    if isinstance(Value, PcurveNode):
        return MakePcurveNode(Value)
    if isinstance(Value, TcoedgeNode):
        return MakeTcoedgeNode(Value)
    if isinstance(Value, TedgeNode):
        return MakeTedgeNode(Value)
    return MakeTvertexNode(Value)
