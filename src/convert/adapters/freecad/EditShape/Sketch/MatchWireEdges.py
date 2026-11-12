from collections import deque as Deque

from convert.adapters.freecad.EditShape.Sketch.WireEdge import SavedEdge
from convert.adapters.freecad.EditShape.Sketch.WireMatch import IsSameEdge, KSketchCurve
from interchange.geometry.models.Transform import Transform


# overlapping tolerance windows need a complete assignment across all saved wires
def IsEdgeMatch(
    Edges: list[SavedEdge],
    Curves: list[KSketchCurve],
    FrameValue: Transform,
    DirectedLines: bool,
) -> bool:
    Owners: dict[int, int] = {}
    Assigned: dict[int, int] = {}
    for EdgeIndex in range(len(Edges)):
        Pending = Deque([EdgeIndex])
        Parents: dict[int, int] = {}
        FreeCurve = None
        while Pending:
            Current = Pending.popleft()
            for CurveIndex, CurveValue in enumerate(Curves):
                if CurveIndex in Parents or not IsSameEdge(
                    Edges[Current], CurveValue, FrameValue, DirectedLines
                ):
                    continue
                Parents[CurveIndex] = Current
                if CurveIndex not in Owners:
                    FreeCurve = CurveIndex
                    break
                Pending.append(Owners[CurveIndex])
            else:
                continue
            break
        while FreeCurve is not None:
            Owner = Parents[FreeCurve]
            Owners[FreeCurve] = Owner
            Previous = Assigned.get(Owner)
            Assigned[Owner] = FreeCurve
            FreeCurve = Previous
        if EdgeIndex not in Assigned:
            return False
    return len(Owners) == len(Curves)
