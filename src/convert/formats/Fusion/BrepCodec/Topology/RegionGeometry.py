from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderCurves import BuildCurves
from convert.formats.Fusion.GeometryCodec.CylinderPlanes import BuildPlanes
from convert.formats.Fusion.GeometryCodec.CylinderPoints import BuildPoints
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def BuildCarriers(Model: CylinderBody) -> tuple[GeometryRecord, ...]:
    return (BuildCurves(Model)[1], BuildPlanes(Model)[1], BuildPoints(Model)[1])
