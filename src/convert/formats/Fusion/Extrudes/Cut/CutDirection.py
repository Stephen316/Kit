from math import dist as Distance

from convert.formats.Fusion.Extrudes.Cut.CutEndData import CutEndData
from interchange.features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorSpace import SpaceVector


# signed depth and explicit through all direction use different stored sign conventions
def CutDirection(Fields: CutEndData, Frame: SupportPlane) -> SpaceVector:
    AxisValue = Frame.transform.z_axis
    Normal = (AxisValue.x, AxisValue.y, AxisValue.z)
    Stored = (Fields.Direction.x, Fields.Direction.y, Fields.Direction.z)
    Blind = Fields.EndValue == ExtrudeEnd.KBlind
    SignValue = 1.0 if Blind else -1.0
    if not Distance(Stored, tuple(SignValue * Value for Value in Normal)) <= 1e-9:
        raise ValueError("Fusion Cut direction disagrees with its saved sketch frame")
    return (
        SpaceVector(-Fields.Direction.x, -Fields.Direction.y, -Fields.Direction.z)
        if Blind
        else Fields.Direction
    )
