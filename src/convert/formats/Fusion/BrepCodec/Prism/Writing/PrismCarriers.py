from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def CurveInterval(Value: float | None) -> tuple[KGeometryValue, ...]:
    return (False,) if Value is None else (True, Value)


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
