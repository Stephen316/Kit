from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Writing.NumberText import NumberText


# the footer operation needs a consistent construction rule so control cage topology retains its native connectivity
def WriteFooter(Header: SurfaceHeader) -> tuple[str, ...]:
    return (
        "",
        "tol " + NumberText(Header.Tolerance),
        "geom-tol " + NumberText(Header.GeometryTol),
        "ver " + str(Header.VersionCount),
        "behavior-version " + Header.BehaviorVersion,
        "compat-version " + Header.CompatVersion,
    )
