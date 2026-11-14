from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderCoedges import BuildCoedges
from convert.formats.Fusion.GeometryCodec.CylinderCurves import BuildCurves
from convert.formats.Fusion.GeometryCodec.CylinderEdges import BuildEdges
from convert.formats.Fusion.GeometryCodec.CylinderFaces import BuildFaces
from convert.formats.Fusion.GeometryCodec.CylinderLoops import BuildLoops
from convert.formats.Fusion.GeometryCodec.CylinderPlanes import BuildPlanes
from convert.formats.Fusion.GeometryCodec.CylinderPoints import BuildPoints
from convert.formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.formats.Fusion.GeometryCodec.CylinderSurface import BuildSurface
from convert.formats.Fusion.GeometryCodec.CylinderVertices import BuildVertices
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def BuildRecords(Model: CylinderBody) -> tuple[GeometryRecord, ...]:
    return (
        *BuildRoots(),
        *BuildFaces(),
        *BuildLoops(),
        *BuildCoedges(),
        *BuildEdges(),
        BuildSurface(Model),
        *BuildPlanes(Model),
        *BuildVertices(),
        *BuildCurves(Model),
        *BuildPoints(Model),
    )
