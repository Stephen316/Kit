from convert.formats.Fusion.TSplineCodec.Model.GripMapping import GripMapping
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

# weight slack must remain consistent across callers so surface geometry retains the control cage shape
KWeightSlack = 2.0**-51

# span limit needs one explicit bound so spline conversion cannot accept inconsistent resource or layout limits
KSpanLimit = 4096.0


# invalid grid cage input must fail here so surface geometry retains the control cage shape
def CheckGridCage(Surface: TsplineSurface) -> GripMapping:
    Header, Topology = Surface.Header, Surface.Topology
    if (Header.Degree, Header.UnitScale, Header.EndConditions) != (
        3,
        1.0,
        "SUBD_CREASES",
    ):
        raise ValueError("Fusion grid conversion needs the cubic crease profile")
    if Surface.Mapping is None:
        raise ValueError("Fusion grid conversion needs boundary compound grips")
    Intervals = {CageEdge.KnotInterval for CageEdge in Topology.Edges}
    if len(Intervals) != 1:
        raise ValueError(
            "Fusion grid conversion needs one knot interval for every edge"
        )
    Interval = Intervals.pop()
    if not Interval.is_integer() or not 1.0 <= Interval <= KSpanLimit:
        raise ValueError("Fusion grid conversion needs a whole-number knot interval")
    if any(Condition.EndValue != 0.0 for Condition in Topology.EndConditions):
        raise ValueError("Fusion grid conversion needs zero end conditions")
    if any(abs(GripValue.Weight - 1.0) > KWeightSlack for GripValue in Surface.Grips):
        raise ValueError("Fusion grid conversion needs unit grip weights")
    RimEdges = {
        LinkValue.EdgeIndex for LinkValue in Topology.Links if LinkValue.FaceIndex == -1
    }
    RimVertices = {
        LinkValue.VertexIndex
        for LinkValue in Topology.Links
        if LinkValue.FaceIndex == -1
    }
    Creases = Surface.Creases
    if Creases is not None and (
        not set(Creases.EdgeIndices) <= RimEdges
        or not set(Creases.VertexIndices) <= RimVertices
    ):
        raise ValueError("Fusion grid conversion does not convert interior creases")
    return Surface.Mapping
