from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.MakeRule import MakeRule
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.RuleWords import (
    KCurveCall,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeCoedgeNode import (
    MakeCoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeEdgeNode import (
    MakeEdgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeVertexNode import (
    MakeVertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    FloatWord,
    IntWord,
    RefWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeTcoedgeNode(Value: TcoedgeNode) -> AsmRecord:
    return AsmRecord(
        "tcoedge-coedge",
        (
            *MakeCoedgeNode(Value.Base).Tokens,
            FloatWord(Value.RangeLower),
            FloatWord(Value.RangeUpper),
            RefWord(Value.CurveRef),
            IntWord(Value.CurveForm),
            *MakeRule(KCurveCall, Value.Curve),
            IntWord(Value.Stamp),
        ),
    )


def MakeTedgeNode(Value: TedgeNode) -> AsmRecord:
    return AsmRecord(
        "tedge-edge",
        (
            *MakeEdgeNode(Value.Base).Tokens,
            FloatWord(Value.Tolerance),
            IntWord(Value.SaveVersion),
            IntWord(Value.Stamp),
        ),
    )


def MakeTvertexNode(Value: TvertexNode) -> AsmRecord:
    return AsmRecord(
        "tvertex-vertex",
        (
            *MakeVertexNode(Value.Base).Tokens,
            FloatWord(Value.Sentinel),
            FloatWord(Value.Tolerance),
            FloatWord(Value.SavedTolerance),
            IntWord(Value.Stamp),
        ),
    )
