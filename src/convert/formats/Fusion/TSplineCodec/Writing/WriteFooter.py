from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Writing.NumberText import NumberText


def WriteFooter(Header: SurfaceHeader) -> tuple[str, ...]:
    return (
        "",
        "tol " + NumberText(Header.Tolerance),
        "geom-tol " + NumberText(Header.GeometryTol),
        "ver " + str(Header.VersionCount),
        "behavior-version " + Header.BehaviorVersion,
        "compat-version " + Header.CompatVersion,
    )
