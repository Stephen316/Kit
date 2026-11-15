from tests.convert.formats.FusionCodec.Brep.GeometryState.NativeGeometry import (
    NativeGeometry,
)


# shared native round setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def NativeRound(Label: str) -> bytes:
    return NativeGeometry(f"re/Fusion/LocalOracle/RoundCarriers/{Label}.f3d")
