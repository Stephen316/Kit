from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.PatchSheet import (
    BoundaryCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface


def GridBounds(Surface: NubsSurface) -> tuple[BsCurve, BsCurve, BsCurve, BsCurve]:
    Plain = BsSurface(
        False,
        "",
        Surface.DegreeU,
        Surface.DegreeV,
        Surface.ClosureU,
        Surface.ClosureV,
        Surface.SingularU,
        Surface.SingularV,
        tuple(KnotValue.Value for KnotValue in Surface.KnotsU),
        tuple(KnotValue.Count for KnotValue in Surface.KnotsU),
        tuple(KnotValue.Value for KnotValue in Surface.KnotsV),
        tuple(KnotValue.Count for KnotValue in Surface.KnotsV),
        Surface.Points,
        (),
    )
    return (
        BoundaryCurve(Plain, 0),
        BoundaryCurve(Plain, 1),
        NegateCurve(BoundaryCurve(Plain, 2)),
        NegateCurve(BoundaryCurve(Plain, 3)),
    )
