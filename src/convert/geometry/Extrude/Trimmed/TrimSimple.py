# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import dist as Distance

from convert.geometry.Extrude.Trimmed.TrimArcHits import GetArcLineHits
from convert.geometry.Extrude.Trimmed.TrimCircleHits import GetArcArcHits
from convert.geometry.Extrude.Trimmed.TrimLineHits import GetLineHits
from convert.geometry.Extrude.Trimmed.TrimOperand import TrimOperand
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# each bounded pair uses the analytic intersection rule for its two carriers
def GetTrimHits(
    First: TrimOperand, Second: TrimOperand, Tolerance: float
) -> tuple[PlaneVector, ...]:
    LeftValue, Right = First.Geometry, Second.Geometry
    if isinstance(LeftValue, ArcGeometry):
        if isinstance(Right, ArcGeometry):
            return GetArcArcHits(LeftValue, Right, Tolerance)
        return GetArcLineHits(LeftValue, Second, Tolerance)
    if isinstance(Right, ArcGeometry):
        return GetArcLineHits(Right, First, Tolerance)
    return GetLineHits(First, Second)


# a simple loop may meet only at its paired endpoints including both ends of a lens
def CheckTrimSimple(
    Parts: tuple[TrimOperand, ...],
    Points: tuple[PlaneVector, ...],
    Matches: tuple[int, ...],
    Tolerance: float,
) -> None:
    for Index, First in enumerate(Parts):
        for Other in range(Index + 1, len(Parts)):
            Shared = tuple(
                Points[Endpoint]
                for Endpoint in (2 * Index, 2 * Index + 1)
                if Matches[Endpoint] // 2 == Other
            )
            for Point in GetTrimHits(First, Parts[Other], Tolerance):
                if not any(
                    Distance((Point.x, Point.y), (Joint.x, Joint.y)) <= Tolerance
                    for Joint in Shared
                ):
                    raise ValueError(
                        "Extrude trim boundary crosses or touches away from a shared endpoint"
                    )
