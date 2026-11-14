from convert.formats.Fusion.GeometryCodec.CylinderCoedges import BuildCoedges
from convert.formats.Fusion.GeometryCodec.CylinderEdges import BuildEdges
from convert.formats.Fusion.GeometryCodec.CylinderFaces import BuildFaces
from convert.formats.Fusion.GeometryCodec.CylinderLoops import BuildLoops
from convert.formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.formats.Fusion.GeometryCodec.CylinderVertices import BuildVertices
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumCurves import FrustumCurves
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumPlanes import FrustumPlanes
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumPoints import FrustumPoints
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumSurface import FrustumSurface
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


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
