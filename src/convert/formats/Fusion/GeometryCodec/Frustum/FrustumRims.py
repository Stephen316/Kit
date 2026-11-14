from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def FrustumRims(
    Model: FrustumBody,
) -> tuple[tuple[tuple[float, float, float], float], ...]:
    CoordX, CoordY, CoordZ = Model.BasePoint
    return (
        ((CoordX, CoordY, CoordZ + Model.Height), Model.TopRadius),
        (Model.BasePoint, Model.BottomRadius),
    )
