from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapPlaces import (
    KPolePlace,
    FacePlan,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    KEndCount,
    CornerPoint,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleLimit import LimitRow
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleMesh import PoleMesh
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import KPoleRow


def FixedSpot(KnotList: tuple[Fraction, ...], Value: Fraction) -> int | None:
    for Index in range(len(KnotList) - KEndCount - 1):
        if KnotList[Index + 1 : Index + KEndCount + 1] == (Value,) * KEndCount:
            return Index
    return None


def FixedRows(
    Graph: CageGraph,
    PlanValue: FacePlan,
    Context: tuple[PoleMesh, int],
    Fixed: frozenset[int],
) -> dict[KPolePlace, KPoleRow]:
    MeshValue, Scale = Context
    Found: dict[KPolePlace, KPoleRow] = {}
    for CellValue in PlanValue.Cells:
        for Corner, LinkIndex in enumerate(Graph.Loops[CellValue.Face]):
            Vertex = Graph.Links[LinkIndex].VertexIndex
            if Vertex not in Fixed:
                continue
            PointU, PointV = CornerPoint(CellValue, Scale, Corner)
            Column = FixedSpot(PlanValue.FullU, PointU)
            RowIndex = FixedSpot(PlanValue.FullV, PointV)
            if Column is not None and RowIndex is not None:
                Found[(RowIndex, Column)] = LimitRow(MeshValue, Vertex, 0)
    return Found
