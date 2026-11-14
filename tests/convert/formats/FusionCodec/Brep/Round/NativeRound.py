from tests.convert.formats.FusionCodec.Brep.GeometryState.NativeGeometry import (
    NativeGeometry,
)


def NativeRound(Label: str) -> bytes:
    return NativeGeometry(f"re/Fusion/LocalOracle/RoundCarriers/{Label}.f3d")
