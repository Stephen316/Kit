from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckConeFrame import (
    CheckConeFrame,
)
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckRimFrame import (
    CheckRimFrame,
)
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# invalid frame input must fail here so circular boundaries retain consistent cone and rim geometry
def CheckFrame(Model: FrustumBody, Frame: FrustumFrame) -> None:
    CheckConeFrame(Model, Frame.Surface)
    CheckRimFrame(Model, Frame.Upper, True)
    CheckRimFrame(Model, Frame.Lower, False)
