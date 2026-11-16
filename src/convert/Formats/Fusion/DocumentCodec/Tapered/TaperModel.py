from math import radians as Radians, tan as Tangent

from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# taper model needs an explicit validity boundary so model state retains its native feature and ownership relationships
def TaperModel(SpecValue: DocumentSpec) -> FrustumBody:
    UpperRadius = SpecValue.RadiusMm + SpecValue.LengthMm * Tangent(
        Radians(SpecValue.TaperDegrees)
    )
    if SpecValue.TaperDegrees != 0.0 and UpperRadius == SpecValue.RadiusMm:
        raise ValueError("Taper angle exceeds dimensional floating-point precision")
    return FrustumBody(
        SpecValue.RadiusMm, UpperRadius, SpecValue.LengthMm, (0.0, 0.0, 0.0)
    )
