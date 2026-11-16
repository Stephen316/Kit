from convert.Formats.Fusion.GeometryCodec.CylinderCoedges import BuildCoedges
from convert.Formats.Fusion.GeometryCodec.CylinderEdges import BuildEdges
from convert.Formats.Fusion.GeometryCodec.CylinderFaces import BuildFaces
from convert.Formats.Fusion.GeometryCodec.CylinderLoops import BuildLoops
from convert.Formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.Formats.Fusion.GeometryCodec.CylinderVertices import BuildVertices
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumCurves import FrustumCurves
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumPlanes import FrustumPlanes
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumPoints import FrustumPoints
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumSurface import FrustumSurface
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the frustum records contract needs a shared interpretation so geometric values retain their native record boundaries
def FrustumRecords(Model: FrustumBody) -> tuple[GeometryRecord, ...]:
    return (
        *BuildRoots(),
        *BuildFaces(),
        *BuildLoops(),
        *BuildCoedges(),
        *BuildEdges(),
        FrustumSurface(Model),
        *FrustumPlanes(Model),
        *BuildVertices(),
        *FrustumCurves(Model),
        *FrustumPoints(Model),
    )
