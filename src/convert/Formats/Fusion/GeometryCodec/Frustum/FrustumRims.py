from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# the frustum rims contract needs a shared interpretation so geometric values retain their native record boundaries
def FrustumRims(
    Model: FrustumBody,
) -> tuple[tuple[tuple[float, float, float], float], ...]:
    CoordX, CoordY, CoordZ = Model.BasePoint
    return (
        ((CoordX, CoordY, CoordZ + Model.Height), Model.TopRadius),
        (Model.BasePoint, Model.BottomRadius),
    )
