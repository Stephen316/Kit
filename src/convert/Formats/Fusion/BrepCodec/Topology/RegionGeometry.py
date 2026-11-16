from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderCurves import BuildCurves
from convert.Formats.Fusion.GeometryCodec.CylinderPlanes import BuildPlanes
from convert.Formats.Fusion.GeometryCodec.CylinderPoints import BuildPoints
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the carriers operation needs a consistent construction rule so topology identity survives native history reconstruction
def BuildCarriers(Model: CylinderBody) -> tuple[GeometryRecord, ...]:
    return (BuildCurves(Model)[1], BuildPlanes(Model)[1], BuildPoints(Model)[1])
