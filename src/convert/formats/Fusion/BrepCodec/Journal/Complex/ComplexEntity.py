from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import (
    IntcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)

KComplexEntity: TypeAlias = (  # lgtm[py/unused-global-variable]
    SplineNode | IntcurveNode | PcurveNode | TcoedgeNode | TedgeNode | TvertexNode
)

KComplexTypes = (
    SplineNode,
    IntcurveNode,
    PcurveNode,
    TcoedgeNode,
    TedgeNode,
    TvertexNode,
)
