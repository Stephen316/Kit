from typing import TypeAlias

from convert.Formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import (
    IntcurveNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)

# the complex entity variants need one shared contract so complex journal geometry cannot omit a supported value shape
KComplexEntity: TypeAlias = (  # lgtm[py/unused-global-variable]
    SplineNode | IntcurveNode | PcurveNode | TcoedgeNode | TedgeNode | TvertexNode
)

# the complex types order must stay explicit so nested spline and surface records retain their relationships
KComplexTypes = (
    SplineNode,
    IntcurveNode,
    PcurveNode,
    TcoedgeNode,
    TedgeNode,
    TvertexNode,
)
