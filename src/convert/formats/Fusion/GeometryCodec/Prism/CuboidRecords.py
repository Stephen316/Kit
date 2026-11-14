from convert.formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.formats.Fusion.GeometryCodec.Prism.CuboidCorners import CuboidCorners
from convert.formats.Fusion.GeometryCodec.Prism.PrismCoedges import BuildCoedges
from convert.formats.Fusion.GeometryCodec.Prism.PrismCurves import BuildCurves
from convert.formats.Fusion.GeometryCodec.Prism.PrismEdges import BuildEdges
from convert.formats.Fusion.GeometryCodec.Prism.PrismFaces import BuildFaces
from convert.formats.Fusion.GeometryCodec.Prism.PrismLoops import BuildLoops
from convert.formats.Fusion.GeometryCodec.Prism.PrismPlanes import BuildPlanes
from convert.formats.Fusion.GeometryCodec.Prism.PrismPoints import BuildPoints
from convert.formats.Fusion.GeometryCodec.Prism.PrismVertices import BuildVertices


def CuboidRecords(Model: CuboidBody) -> tuple[GeometryRecord, ...]:
    Corners = CuboidCorners(Model)
    UseValues = BuildUses()
    return (
        *BuildRoots(),
        *BuildFaces(),
        *BuildLoops(),
        *BuildCoedges(UseValues),
        *BuildEdges(UseValues),
        *BuildPlanes(Corners),
        *BuildVertices(),
        *BuildCurves(Corners),
        *BuildPoints(Corners),
    )
