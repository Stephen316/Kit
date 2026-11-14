from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


def CuboidCorners(Model: CuboidBody) -> tuple[tuple[float, float, float], ...]:
    CoordX, CoordY, CoordZ = Model.BasePoint
    return tuple(
        (
            CoordX + (Model.Width if Corner & 1 else 0),
            CoordY + (Model.Depth if Corner & 2 else 0),
            CoordZ + (Model.Height if Corner & 4 else 0),
        )
        for Corner in range(8)
    )
