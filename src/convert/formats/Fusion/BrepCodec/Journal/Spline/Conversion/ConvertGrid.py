from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.CheckGridCage import (
    CheckGridCage,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridBounds import (
    GridBounds,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridJumps import (
    GridJumps,
    ThirdJumps,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridKnots import (
    GridKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridPatches import (
    GridPatches,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridResult import (
    GridResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.PlaceGrips import (
    PlaceGrips,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.PlaceVertices import (
    PlaceVertices,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.SpokeIndices import (
    SpokeIndices,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def ScaleJumps(
    Lists: tuple[tuple[float, ...], ...], Scale: int
) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(KnotValue * Scale for KnotValue in Values) for Values in Lists)


def ConvertGrid(Surface: TsplineSurface) -> GridResult:
    CheckSurface(Surface)
    Mapping = CheckGridCage(Surface)
    Scale = int(Surface.Topology.Edges[0].KnotInterval)
    Spokes = SpokeIndices(Surface.Topology)
    Places = PlaceVertices(Surface.Topology, Spokes)
    Width, Height, Order = PlaceGrips(Mapping, Places, len(Surface.Grips))
    Grips = tuple(Surface.Grips[Index] for Index in Order)
    Points = tuple(
        (GripValue.CoordX, GripValue.CoordY, GripValue.CoordZ) for GripValue in Grips
    )
    UnitSurface = NubsSurface(
        3, 3, 0, 0, 0, 0, GridKnots(Width - 3, 1), GridKnots(Height - 3, 1), Points
    )
    Result = ReplaceValue(
        UnitSurface,
        KnotsU=GridKnots(Width - 3, Scale),
        KnotsV=GridKnots(Height - 3, Scale),
    )
    Corners = (Points[0], Points[Width - 1], Points[-1], Points[-Width])
    UnitJumps = tuple(ThirdJumps(Bound) for Bound in GridBounds(UnitSurface))
    return GridResult(
        Result,
        GridPatches(Surface.Topology, Spokes, Places, Scale),
        GridBounds(Result),
        Corners,
        ScaleJumps(GridJumps(UnitSurface, Width, Height), Scale),
        ScaleJumps(UnitJumps, Scale),
    )
