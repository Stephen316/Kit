from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.CageOrientation import (
    CageOrientation,
)
from convert.formats.Fusion.TSplineCodec.Authoring.MakeLinks import MakeLinks
from convert.formats.Fusion.TSplineCodec.Authoring.MakeTopology import MakeTopology
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def MakeClosedCage(
    Vertices: tuple[ControlGrip, ...],
    Faces: tuple[tuple[int, ...], ...],
    Header: SurfaceHeader | None = None,
    Orientation: CageOrientation | None = None,
) -> TsplineSurface:
    if not 0 < len(Vertices) <= 1000000 or not 0 < len(Faces) <= 250000:
        raise ValueError("TSM authoring allocation exceeds the limit")
    Links = MakeLinks(Faces, len(Vertices))
    Result = TsplineSurface(
        Header or SurfaceHeader(),
        MakeTopology(Links, len(Vertices), Orientation),
        Vertices,
    )
    CheckSurface(Result)
    return Result
