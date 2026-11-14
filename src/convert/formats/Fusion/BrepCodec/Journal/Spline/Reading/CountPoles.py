from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


def CountPoles(Knots: tuple[SplineKnot, ...], Degree: int) -> int:
    if not 1 <= Degree <= 15 or not 2 <= len(Knots) <= 1024:
        raise ValueError("Unsupported Fusion spline degree or knot count")
    if any(not 1 <= KnotValue.Count <= Degree for KnotValue in Knots):
        raise ValueError("Invalid Fusion spline knot multiplicity")
    if any(Prior.Value >= Later.Value for Prior, Later in zip(Knots, Knots[1:])):
        raise ValueError("Fusion spline knots must strictly increase")
    Poles = sum(KnotValue.Count for KnotValue in Knots) - Degree + 1
    if not Degree < Poles <= 65536:
        raise ValueError("Invalid Fusion spline control point count")
    return Poles
