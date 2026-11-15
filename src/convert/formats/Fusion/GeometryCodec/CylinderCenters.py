from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody


# the centers operation needs a distinct decoding boundary so geometric values retain their native record boundaries
def GetCenters(Model: CylinderBody) -> tuple[tuple[float, float, float], ...]:
    CoordX, CoordY, CoordZ = Model.BasePoint
    return ((CoordX, CoordY, CoordZ + Model.Height), Model.BasePoint)
