from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import FormBody

# parameter slack must remain consistent across callers so editable control cages retain their document relationships
KParamSlack = 1e-9


# the boundary decision must stay consistent so editable control cages retain their document relationships
def IsBoundary(Curve: BsCurve, Bounds: tuple[float, float, float, float]) -> bool:
    return any(
        all(
            abs(PoleValue[AxisIndex] - Boundary) <= KParamSlack
            for PoleValue in Curve.Poles
        )
        for AxisIndex, Boundary in (
            (0, Bounds[0]),
            (0, Bounds[1]),
            (1, Bounds[2]),
            (1, Bounds[3]),
        )
    )


# invalid trimming input must fail here so editable control cages retain their document relationships
def CheckTrimming(Model: FormBody) -> None:
    for FaceValue in Model.Faces:
        Cache = FaceValue.Surface.Cache
        if Cache.ClosureU == 2 or Cache.ClosureV == 2:
            continue
        Bounds = (
            Cache.KnotsU[0].Value,
            Cache.KnotsU[-1].Value,
            Cache.KnotsV[0].Value,
            Cache.KnotsV[-1].Value,
        )
        if any(not IsBoundary(UseValue.Pcurve, Bounds) for UseValue in FaceValue.Uses):
            raise ValueError("Fusion Form mass cache cannot integrate trimmed faces")
