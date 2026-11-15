from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody

# the geometry types order must stay explicit so public document claims remain grounded in native records
KGeometryTypes: tuple[type[object], ...] = (
    CylinderBody,
    FrustumBody,
    GeometryStamp,
    CuboidBody,
)
