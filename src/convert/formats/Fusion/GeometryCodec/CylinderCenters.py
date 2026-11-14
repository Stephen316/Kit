from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody


def GetCenters(Model: CylinderBody) -> tuple[tuple[float, float, float], ...]:
    CoordX, CoordY, CoordZ = Model.BasePoint
    return ((CoordX, CoordY, CoordZ + Model.Height), Model.BasePoint)
