from math import hypot as Hypot, pi as KPiValue, isclose as IsClose

from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def RotaryMass(Context: ExtrudeContext, Model: FrustumBody) -> None:
    Lower, Upper, Height = (
        Model.BottomRadius / 10,
        Model.TopRadius / 10,
        Model.Height / 10,
    )
    Delta = Upper - Lower
    CrossSum = Lower * Lower + Lower * Upper + Upper * Upper
    Volume = KPiValue * Height * CrossSum / 3
    AreaValue = KPiValue * (
        Lower * Lower + Upper * Upper + (Lower + Upper) * Hypot(Height, Delta)
    )
    CenterZ = (
        Height
        * (Lower * Lower + 2 * Lower * Upper + 3 * Upper * Upper)
        / (4 * CrossSum)
    )
    Center = (
        Model.BasePoint[0] / 10,
        Model.BasePoint[1] / 10,
        Model.BasePoint[2] / 10 + CenterZ,
    )
    Fourth = Height * sum(Lower ** (4 - Index) * Upper**Index for Index in range(5)) / 5
    Axial = Height**3 * (Lower**2 / 3 + Lower * Delta / 2 + Delta**2 / 5)
    Central = (
        KPiValue * (Fourth / 4 + Axial) - Volume * CenterZ**2,
        KPiValue * Fourth / 2,
    )
    Inertia = tuple(
        (Central[1] if Index == 2 else Central[0])
        + Volume * sum(Center[Other] ** 2 for Other in range(3) if Other != Index)
        for Index in range(3)
    )
    CrossTerms = tuple(
        -Volume * Center[First] * Center[Second]
        for First, Second in ((0, 1), (0, 2), (1, 2))
    )
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
    CacheNumbers(
        (NumberValue(Cache["volume"]), NumberValue(Cache["area"])), (Volume, AreaValue)
    )
    CacheNumbers(PointCoords(Cache["cog"]), Center)
    CacheNumbers(PointCoords(Cache["moi"]), Inertia)
    CacheNumbers(PointCoords(Cache["moiOffDiag"]), CrossTerms)


def CacheNumbers(Actual: tuple[float, ...], Expected: tuple[float, ...]) -> None:
    if len(Actual) != len(Expected) or any(
        not IsClose(First, Second, rel_tol=1e-6, abs_tol=1e-8)
        for First, Second in zip(Actual, Expected, strict=True)
    ):
        raise ValueError("Native circular mass cache disagrees with analytic geometry")
