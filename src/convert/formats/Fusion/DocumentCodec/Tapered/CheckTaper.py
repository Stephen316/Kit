from math import isfinite as IsFinite

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Tapered.TaperModel import TaperModel


def CheckTaper(SpecValue: DocumentSpec) -> None:
    AngleValue = SpecValue.TaperDegrees
    if (
        type(AngleValue) not in (int, float)
        or not IsFinite(AngleValue)
        or not -90.0 < AngleValue < 90.0
    ):
        raise ValueError("Taper must be finite degrees strictly between -90 and 90")
    if SpecValue.ProfileKind != "frustum" and AngleValue != 0.0:
        raise ValueError("A nonzero taper requires the frustum document profile")
    if SpecValue.ProfileKind == "frustum":
        _ = TaperModel(SpecValue)
