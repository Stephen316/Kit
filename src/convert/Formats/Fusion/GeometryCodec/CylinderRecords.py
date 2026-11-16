from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.CylinderCoedges import BuildCoedges
from convert.Formats.Fusion.GeometryCodec.CylinderCurves import BuildCurves
from convert.Formats.Fusion.GeometryCodec.CylinderEdges import BuildEdges
from convert.Formats.Fusion.GeometryCodec.CylinderFaces import BuildFaces
from convert.Formats.Fusion.GeometryCodec.CylinderLoops import BuildLoops
from convert.Formats.Fusion.GeometryCodec.CylinderPlanes import BuildPlanes
from convert.Formats.Fusion.GeometryCodec.CylinderPoints import BuildPoints
from convert.Formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.Formats.Fusion.GeometryCodec.CylinderSurface import BuildSurface
from convert.Formats.Fusion.GeometryCodec.CylinderVertices import BuildVertices
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the records operation needs a consistent construction rule so geometric values retain their native record boundaries
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
