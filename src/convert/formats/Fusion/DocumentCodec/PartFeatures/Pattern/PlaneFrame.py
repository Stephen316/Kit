from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec

KVector = tuple[float, float, float]
KFrames: dict[str, tuple[KVector, KVector, KVector]] = {
    "xy": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "yz": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    "xz": ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
}


def PointOf(Values: KVector) -> dict[str, float]:
    return {"x": Values[0], "y": Values[1], "z": Values[2]}


def PlaneValue(Feature: PlaneSpec, OffsetCm: float) -> dict[str, object]:
    UAxis, VAxis, Normal = KFrames[Feature.BasePlane]
    Origin = (Normal[0] * OffsetCm, Normal[1] * OffsetCm, Normal[2] * OffsetCm)
    return {
        "normalReversed": False,
        "origin": PointOf(Origin),
        "uAxis": PointOf(UAxis),
        "vAxis": PointOf(VAxis),
    }


def PlaneMatrix(Feature: PlaneSpec) -> list[float]:
    UAxis, VAxis, Normal = KFrames[Feature.BasePlane]
    OffsetCm = Feature.OffsetMm / 10.0
    Matrix = [
        [UAxis[Index], VAxis[Index], Normal[Index], Normal[Index] * OffsetCm]
        for Index in range(3)
    ]
    return [float(Value) for Entries in Matrix for Value in Entries] + [
        0.0,
        0.0,
        0.0,
        1.0,
    ]
