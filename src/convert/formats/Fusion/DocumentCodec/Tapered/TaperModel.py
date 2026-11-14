from math import radians as Radians, tan as Tangent

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def TaperModel(SpecValue: DocumentSpec) -> FrustumBody:
    UpperRadius = SpecValue.RadiusMm + SpecValue.LengthMm * Tangent(
        Radians(SpecValue.TaperDegrees)
    )
    if SpecValue.TaperDegrees != 0.0 and UpperRadius == SpecValue.RadiusMm:
        raise ValueError("Taper angle exceeds dimensional floating-point precision")
    return FrustumBody(
        SpecValue.RadiusMm, UpperRadius, SpecValue.LengthMm, (0.0, 0.0, 0.0)
    )
