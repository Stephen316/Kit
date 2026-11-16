from convert.Formats.Fusion.GeometryCodec.CylinderRoots import BuildRoots
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidCorners import CuboidCorners
from convert.Formats.Fusion.GeometryCodec.Prism.PrismCoedges import BuildCoedges
from convert.Formats.Fusion.GeometryCodec.Prism.PrismCurves import BuildCurves
from convert.Formats.Fusion.GeometryCodec.Prism.PrismEdges import BuildEdges
from convert.Formats.Fusion.GeometryCodec.Prism.PrismFaces import BuildFaces
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLoops import BuildLoops
from convert.Formats.Fusion.GeometryCodec.Prism.PrismPlanes import BuildPlanes
from convert.Formats.Fusion.GeometryCodec.Prism.PrismPoints import BuildPoints
from convert.Formats.Fusion.GeometryCodec.Prism.PrismVertices import BuildVertices


# the cuboid records contract needs a shared interpretation so geometric values retain their native record boundaries
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
