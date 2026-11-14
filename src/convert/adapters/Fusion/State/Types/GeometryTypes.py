from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody

KGeometryTypes: tuple[type[object], ...] = (
    CylinderBody,
    FrustumBody,
    GeometryStamp,
    CuboidBody,
)
