def MakePoint(
    CoordX: float = 0.0, CoordY: float = 0.0, CoordZ: float = 0.0
) -> dict[str, object]:
    return {"x": CoordX, "y": CoordY, "z": CoordZ}


def MakeColor(
    RedValue: float = 0.0,
    GreenValue: float = 0.0,
    BlueValue: float = 0.0,
    AlphaValue: float = 1.0,
) -> dict[str, object]:
    return dict(red=RedValue, green=GreenValue, blue=BlueValue, alpha=AlphaValue)
