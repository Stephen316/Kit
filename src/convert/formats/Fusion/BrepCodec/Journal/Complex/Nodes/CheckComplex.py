from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode


def CheckFormSign(Entities: tuple[KJournalEntity, ...], Coedge: CoedgeNode) -> None:
    if not 0 <= Coedge.Pcurve < len(Entities):
        return
    Pcurve = Entities[Coedge.Pcurve]
    if not isinstance(Pcurve, PcurveNode) or not Pcurve.Form:
        return
    if (Pcurve.Form > 0) != (Coedge.Reversed == Pcurve.Reversed):
        raise ValueError("Fusion pcurve form sign disagrees with its coedge sense")


def CheckTolerance(Entities: tuple[KJournalEntity, ...], Tolerant: TedgeNode) -> None:
    for Vertex in (Tolerant.Base.StartVertex, Tolerant.Base.EndVertex):
        Value = Entities[Vertex] if 0 <= Vertex < len(Entities) else None
        if isinstance(Value, TvertexNode) and Value.Tolerance < Tolerant.Tolerance:
            raise ValueError("Fusion tolerant vertex is tighter than its tolerant edge")


def CheckComplex(Entities: tuple[KJournalEntity, ...]) -> None:
    for Value in Entities:
        if isinstance(Value, TcoedgeNode):
            CheckFormSign(Entities, Value.Base)
        elif isinstance(Value, CoedgeNode):
            CheckFormSign(Entities, Value)
        elif isinstance(Value, TedgeNode):
            CheckTolerance(Entities, Value)
