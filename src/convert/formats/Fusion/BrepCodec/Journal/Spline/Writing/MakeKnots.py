from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


def MakeKnots(Knots: tuple[SplineKnot, ...]) -> tuple[KAsmToken, ...]:
    return (4, len(Knots)), *(
        Field
        for KnotValue in Knots
        for Field in ((6, KnotValue.Value), (4, KnotValue.Count))
    )
