from dataclasses import dataclass as Dataclass
from math import isfinite as IsFinite

from HeaderTail import HeaderBounds, Point
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# each default datum has a fixed affine frame independent of its visual border
@Dataclass(frozen=True, slots=True)
class PrincipalFrame:
    Normal: Point
    Basis: tuple[float, ...] | None
    UAxis: int
    VAxis: int
    USign: int
    VSign: int


# front top and right use the three native world orientations in that order
KPrincipalFrames = (
    PrincipalFrame((0.0, 0.0, 1.0), None, 0, 1, 1, 1),
    PrincipalFrame(
        (0.0, 1.0, 0.0), (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0), 0, 2, 1, -1
    ),
    PrincipalFrame(
        (1.0, 0.0, 0.0), (-0.0, 0.0, 1.0, -0.0, 1.0, 0.0, -1.0, 0.0, 0.0), 2, 1, -1, 1
    ),
)


# the native length tolerance selects the surviving span for an edge on projection
KBorderTolerance = 1e-7


# border dimensions and name location change when the owning model updates
@Dataclass(frozen=True, slots=True)
class PlaneView:
    NamePoint: tuple[float, ...]
    Border: tuple[float, ...]
    DisplayRoot: tuple[float, ...]


# converting through signed plane axes keeps the name corner on its actual datum
def PlanePoint(Frame: PrincipalFrame, UValue: float, VValue: float) -> Point:
    PointValue = [0.0, 0.0, 0.0]
    PointValue[Frame.UAxis] = Frame.USign * UValue
    PointValue[Frame.VAxis] = Frame.VSign * VValue
    return (PointValue[0], PointValue[1], PointValue[2])


# the two dimensional display uses projected bounds rather than the solid thickness alone
def BuildPlaneView(Frame: PrincipalFrame, Bounds: HeaderBounds) -> PlaneView:
    Low, High = Bounds.Minimum, Bounds.Maximum
    RequireArch(
        all(
            IsFinite(A) and IsFinite(B) and A <= B
            for A, B in zip(Low, High, strict=True)
        ),
        True,
        "finite ordered model bounds for principal datum",
    )
    SpanU = High[Frame.UAxis] - Low[Frame.UAxis]
    SpanV = High[Frame.VAxis] - Low[Frame.VAxis]
    RequireArch(
        max(SpanU, SpanV) >= KBorderTolerance, True, "finite datum projection span"
    )
    if SpanU < KBorderTolerance:
        SpanU = SpanV
    if SpanV < KBorderTolerance:
        SpanV = SpanU
    HalfU, HalfV = SpanU * 0.5 + SpanU * 0.05, SpanV * 0.5 + SpanV * 0.05
    CenterU = Frame.USign * (Low[Frame.UAxis] + High[Frame.UAxis]) * 0.5
    CenterV = Frame.VSign * (Low[Frame.VAxis] + High[Frame.VAxis]) * 0.5
    Return = PlaneView(
        PlanePoint(Frame, CenterU - HalfU, CenterV + HalfV),
        (HalfU, -HalfU, HalfV, -HalfV),
        PlanePoint(Frame, CenterU, CenterV),
    )
    RequirePlaneView(Return)
    return Return


# each presentation record remains a finite and properly framed principal display
def RequirePlaneView(View: PlaneView) -> None:
    RequireArch(
        (len(View.NamePoint), len(View.Border), len(View.DisplayRoot)),
        (3, 4, 3),
        "principal plane presentation widths",
    )
    RequireArch(
        all(map(IsFinite, (*View.NamePoint, *View.Border, *View.DisplayRoot))),
        True,
        "finite principal plane presentation",
    )
    MaxU, MinU, MaxV, MinV = View.Border
    RequireArch(
        MaxU > 0.0 and MaxV > 0.0 and MaxU == -MinU and MaxV == -MinV,
        True,
        "centered principal plane border",
    )
