from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Topology.CutResult.CutMetricBox import CutMetricBox


# each box boundary has an explicit plane and pocket role independent of loop order
@MakeDataClass(frozen=True, slots=True)
class CutMetricLoop:
    AxisIndex: int
    HighSide: bool
    Cavity: bool
    Opening: bool

    # the opening and its surrounding rim must have the same native face owner
    def FaceGroup(self) -> tuple[int, bool, bool]:
        return self.AxisIndex, self.HighSide, self.Cavity and not self.Opening

    # the cavity bounds the removed material so its winding faces inward
    def RingSense(self) -> int:
        return 1 if self.HighSide != self.Cavity else -1

    # hole winding reverses against its enclosing face normal
    def FaceSense(self) -> int:
        return -self.RingSense() if self.Opening else self.RingSense()


# native vertex ids distinguish each expected rectangle before any geometric comparison
def MetricLoops(
    Outer: CutMetricBox, Inner: CutMetricBox, CutAxis: int, Openings: frozenset[bool]
) -> dict[frozenset[int], CutMetricLoop]:
    Expected: dict[frozenset[int], CutMetricLoop] = {}
    for BoxValue, Cavity in ((Outer, False), (Inner, True)):
        for Index in range(3):
            for HighSide in (False, True):
                Identity = frozenset(
                    Vertex
                    for Corner, Vertex in BoxValue.Corners.items()
                    if Corner[Index] == HighSide
                )
                Expected[Identity] = CutMetricLoop(
                    Index,
                    HighSide,
                    Cavity,
                    Cavity and Index == CutAxis and HighSide in Openings,
                )
    return Expected
