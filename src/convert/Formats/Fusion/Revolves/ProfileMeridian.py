from convert.Formats.Fusion.Revolves.MeridianSense import ChooseMeridian
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# both angular and plane limits use the same occupied line profile half plane
def CalcMeridian(
    SketchFrame: Transform,
    ProfileLines: tuple[LineGeometry, ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if len(ProfileLines) not in (3, 4):
        raise ValueError("Fusion Revolve requires a three or four line profile")
    Points = tuple(
        Point
        for LineValue in ProfileLines
        for Point in (LineValue.start, LineValue.end)
    )
    return ChooseMeridian(SketchFrame, Points, AxisOrigin, AxisDirection)
