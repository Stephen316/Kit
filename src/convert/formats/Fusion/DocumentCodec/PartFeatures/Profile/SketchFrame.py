from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint

KFrontMatrix = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    -1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def FrameAxes(
    PlaneRole: str, LiftCm: float = 0.0
) -> tuple[dict[str, object], dict[str, object]]:
    if PlaneRole == "xz_plane" and not LiftCm:
        return MakePoint(0.0, 0.0, 1.0), MakePoint(1.0)
    if PlaneRole != "xy_plane" and not LiftCm:
        raise ValueError("Fusion part sketches lie on the XY or XZ plane")
    return MakePoint(1.0), MakePoint(0.0, 1.0)


def FrameMatrix(PlaneRole: str, LiftCm: float = 0.0) -> dict[str, object]:
    if LiftCm:
        Entries = [0.0] * 16
        for Index in (0, 5, 10, 15):
            Entries[Index] = 1.0
        Entries[11] = LiftCm
        return {"entries": Entries}
    if PlaneRole == "xz_plane":
        return {"entries": list(KFrontMatrix)}
    return {}


def FrameNormal(PlaneRole: str) -> dict[str, object]:
    if PlaneRole == "xz_plane":
        return MakePoint(KFrontMatrix[2], KFrontMatrix[6], KFrontMatrix[10])
    return MakePoint(0.0, 0.0, 1.0)
