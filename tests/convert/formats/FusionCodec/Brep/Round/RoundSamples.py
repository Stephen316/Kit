from convert.formats.Fusion.BrepCodec.Journal.Round.SphereBody import SphereBody
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusBody import TorusBody
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

# the round history cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRoundHistory = HistoryState(7, 2, 7, 1, 2, 7)

# the round stamp cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRoundStamp = GeometryStamp(
    "Kit archive integration", "ASM 232.5.0.65535 OSX", "independent analytic geometry"
)

# the round bodies cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRoundBodies = (
    SphereBody(19.0, (-11.0, 7.0, 13.0)),
    TorusBody(31.0, 9.0, (17.0, -13.0, 5.0)),
    TorusBody(31.0, 9.0, (17.0, -13.0, 5.0), (0.0, 0.6, 0.8)),
)
