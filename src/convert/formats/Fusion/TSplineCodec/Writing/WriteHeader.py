from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Writing.NumberText import NumberText


def WriteHeader(Header: SurfaceHeader) -> tuple[str, ...]:
    return (
        "#TS0200",
        "",
        "degree " + str(Header.Degree),
        "cap-type " + Header.CapType,
        "star-smoothness " + NumberText(Header.StarSmoothness),
        "units " + NumberText(Header.UnitScale) + " " + Header.UnitName,
        "end-conditions " + Header.EndConditions,
        "star-knot-rule " + Header.StarKnotRule,
    )
