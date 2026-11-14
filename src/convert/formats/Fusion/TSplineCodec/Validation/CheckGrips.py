from math import isfinite
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices
from convert.formats.Fusion.TSplineCodec.Validation.CheckCompounds import CheckCompounds


def CheckGrips(Surface: TsplineSurface) -> None:
    if not 0 < len(Surface.Grips) <= 1000000:
        raise ValueError("Invalid TSM grip allocation")
    for GripValue in Surface.Grips:
        if (
            not all(
                isfinite(Value)
                for Value in (GripValue.CoordX, GripValue.CoordY, GripValue.CoordZ)
            )
            or not isfinite(GripValue.Weight)
            or GripValue.Weight <= 0.0
        ):
            raise ValueError("Unsupported TSM weighted control point")
    if Surface.Mapping is None:
        if len(Surface.Grips) != len(Surface.Topology.Vertices):
            raise ValueError("TSM implicit grip map differs from vertices")
    else:
        Owners = Surface.Mapping.Owners
        if len(Owners) != len(Surface.Grips) or any(
            type(Value.IsPrimary) is not bool for Value in Owners
        ):
            raise ValueError("TSM grip ownership allocation differs")
        CheckIndices(
            tuple(Value.VertexIndex for Value in Owners),
            len(Surface.Topology.Vertices),
            "grip owner",
            False,
        )
        Primary = tuple(Value.VertexIndex for Value in Owners if Value.IsPrimary)
        CheckIndices(Primary, len(Surface.Topology.Vertices), "primary grip")
        if set(Primary) != set(range(len(Surface.Topology.Vertices))):
            raise ValueError("TSM primary grips do not cover vertices")
        CheckCompounds(Surface)
    CheckIndices(Surface.SmartGrips, len(Surface.Grips), "smart grip")
