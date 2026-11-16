from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.Formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.Formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.Formats.Fusion.TSplineCodec.Model.CageOrientation import (
    CageOrientation,
)
from convert.Formats.Fusion.TSplineCodec.Authoring.MakeLinks import MakeLinks
from convert.Formats.Fusion.TSplineCodec.Authoring.MakeTopology import MakeTopology
from convert.Formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


# the closed cage operation needs a consistent construction rule so control cage topology retains its native connectivity
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
