from math import hypot as Hypot, isclose as IsClose, isfinite as IsFinite
from struct import pack as PackFields
from sys import float_info as FloatInfo

from BlindDimension import Axes, DimGeometry, DotProduct, KTriple, RequireFrame
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# empty prefix suffix and two callouts have separate saved string fields
KLabelCount = 4

# the display constructor sets its text interpolation halfway along the dimension
KTextPosition = 0.5

# an ordinary distance dimension starts without a radius or extra leader
KRadius = 0.0
KExtraLeader = -1.0

# the default distance display retains its constructor color and smart arrow value
KColor = 5
KSmartArrows = 2

# reference points are expressed relative to the selected display origin
KOrigin = (0.0, 0.0, 0.0)


# the two supplied model vectors establish the presentation axes in the selected frame
def RelativeAxes(Geometry: DimGeometry) -> tuple[KTriple, KTriple]:
    Frame = Geometry.Frame
    Basis = Axes(Frame.x_axis), Axes(Frame.y_axis), Axes(Frame.z_axis)
    RequireFrame(Basis)
    RequireArch(type(Geometry.Reverse), bool, "explicit display direction reversal")
    Normal, Tangent = Axes(Geometry.Normal), Axes(Geometry.Tangent)
    RequireArch(
        IsClose(Hypot(*Normal), 1.0, abs_tol=1e-9, rel_tol=0)
        and IsClose(Hypot(*Tangent), 1.0, abs_tol=1e-9, rel_tol=0)
        and IsClose(DotProduct(Normal, Tangent), 0.0, abs_tol=1e-9, rel_tol=0),
        True,
        "orthogonal unit display vectors",
    )
    First, Second, Third = Basis
    TextDir = (
        DotProduct(Tangent, First),
        DotProduct(Tangent, Second),
        DotProduct(Tangent, Third),
    )
    Sign = -1.0 if Geometry.Reverse else 1.0
    RefDir = (
        Sign * DotProduct(Normal, First),
        Sign * DotProduct(Normal, Second),
        Sign * DotProduct(Normal, Third),
    )
    return TextDir, RefDir


# the outer display placement starts after the referenced model dimension has closed
def EncodeBossTail(
    *,
    Generation: int,
    DisplayMode: int,
    ConditionOne: bool,
    Geometry: DimGeometry,
    DepthMm: float,
    WitnessMetres: float,
    ArrowHead: int,
    Precision: int,
    AltPrecision: int,
) -> bytes:
    RequireArch(
        (Generation, DisplayMode, ConditionOne),
        (KConfigGen, 201, False),
        "witnessed plain blind distance display route",
    )
    RequireArch(
        (ArrowHead, Precision, AltPrecision),
        (0, 2, 2),
        "witnessed document distance display settings",
    )
    RequireArch(
        type(DepthMm) in (int, float)
        and 0 < DepthMm <= FloatInfo.max
        and DepthMm / 1000 > 0,
        True,
        "positive depth for display reference points",
    )
    RequireArch(
        IsFinite(WitnessMetres), True, "finite signed annotation witness projection"
    )
    TextDir, RefDir = RelativeAxes(Geometry)
    Depth = DepthMm / 1000
    RefPoint = tuple(Value * Depth + 0.0 for Value in RefDir)
    return (
        PackFields("<3H", ArrowHead, ArrowHead, 0)
        + EncodeString("") * KLabelCount
        + PackFields(
            "<22di7H3d",
            *TextDir,
            KTextPosition,
            WitnessMetres,
            KRadius,
            KExtraLeader,
            *KOrigin,
            *KOrigin,
            *RefPoint,
            *RefPoint,
            *KOrigin,
            0,  # absent optional reference at display member a50
            0,
            0,
            0,  # empty witness leader and arrow masks
            KColor,
            Precision,
            AltPrecision,
            KSmartArrows,
            *RefDir,
        )
    )
