from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the curve interval contract needs a shared interpretation so profile topology remains connected to its extrusion history
def CurveInterval(Value: float | None) -> tuple[KGeometryValue, ...]:
    return (False,) if Value is None else (True, Value)


# the prism curves contract needs a shared interpretation so profile topology remains connected to its extrusion history
def PrismCurves(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "straight-curve",
            (
                EdgeValue.Curve.OriginCm,
                EdgeValue.Curve.DirectionCm,
                *CurveInterval(EdgeValue.Curve.LowerBound),
                *CurveInterval(EdgeValue.Curve.UpperBound),
            ),
        )
        for EdgeValue in Frame.Edges
    )


# the prism planes contract needs a shared interpretation so profile topology remains connected to its extrusion history
def PrismPlanes(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "plane-surface",
            (
                Value.OriginCm,
                Value.Normal,
                Value.Basis,
                Value.ReverseV,
                False,
                False,
                False,
                False,
            ),
        )
        for Value in Frame.Planes
    )
