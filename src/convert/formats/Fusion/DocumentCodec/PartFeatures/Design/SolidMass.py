from dataclasses import replace as ReplaceValue
from math import hypot as Hypotenuse, sqrt as SquareRoot

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundShape import (
    ApplyRounds,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import (
    LoopArea,
    LoopPolygon,
    SpanArea,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SlabRoof import SlabPairs
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    KFullTurn,
    SpanHeading,
    SpanLength,
)

KGaussNodes = (
    (-SquareRoot(0.6), 5.0 / 9.0),
    (0.0, 8.0 / 9.0),
    (SquareRoot(0.6), 5.0 / 9.0),
)


def PlaneMoments(Polygon: list[tuple[float, float]]) -> dict[str, float]:
    SumValues = dict(x=0.0, y=0.0, xx=0.0, yy=0.0, xy=0.0)
    for Index, (StartX, StartY) in enumerate(Polygon):
        FinishX, FinishY = Polygon[(Index + 1) % len(Polygon)]
        Cross = StartX * FinishY - FinishX * StartY
        SumValues["x"] += (StartX + FinishX) * Cross / 6.0
        SumValues["y"] += (StartY + FinishY) * Cross / 6.0
        SumValues["xx"] += (
            (StartX * StartX + StartX * FinishX + FinishX * FinishX) * Cross / 12.0
        )
        SumValues["yy"] += (
            (StartY * StartY + StartY * FinishY + FinishY * FinishY) * Cross / 12.0
        )
        SumValues["xy"] += (
            (
                StartX * FinishY
                + 2 * StartX * StartY
                + 2 * FinishX * FinishY
                + FinishX * StartY
            )
            * Cross
            / 24.0
        )
    return SumValues


def MixPoint(
    Lower: tuple[float, float], Upper: tuple[float, float], Ratio: float
) -> tuple[float, float]:
    return (
        Lower[0] * (1.0 - Ratio) + Upper[0] * Ratio,
        Lower[1] * (1.0 - Ratio) + Upper[1] * Ratio,
    )


def LoopsAt(SlabValue: PrismSlab, Level: float) -> tuple[KPlaneLoop, ...]:
    Ratio = (Level - SlabValue.LowerCm) / (SlabValue.UpperCm - SlabValue.LowerCm)
    Loops: list[KPlaneLoop] = []
    for LoopValue, RoofValue in SlabPairs(SlabValue):
        Spans: list[KPlaneSpan] = []
        for SpanValue, RoofSpan in zip(LoopValue, RoofValue, strict=True):
            if isinstance(SpanValue, ArcSpan) and isinstance(RoofSpan, ArcSpan):
                Radius = SpanValue.RadiusCm * (1.0 - Ratio) + RoofSpan.RadiusCm * Ratio
                SpanValue = ReplaceValue(SpanValue, RadiusCm=Radius)
            if isinstance(SpanValue, LineSpan) and isinstance(RoofSpan, LineSpan):
                SpanValue = LineSpan(
                    MixPoint(SpanValue.StartCm, RoofSpan.StartCm, Ratio),
                    MixPoint(SpanValue.FinishCm, RoofSpan.FinishCm, Ratio),
                    SpanValue.Label,
                )
            Spans.append(SpanValue)
        Loops.append(tuple(Spans))
    return tuple(Loops)


def TaperMassMut(MassValue: dict[str, float], SlabValue: PrismSlab) -> None:
    Middle = (SlabValue.LowerCm + SlabValue.UpperCm) / 2.0
    HalfValue = (SlabValue.UpperCm - SlabValue.LowerCm) / 2.0
    for Abscissa, Weight in KGaussNodes:
        Level, Scale = Middle + HalfValue * Abscissa, HalfValue * Weight
        Loops = LoopsAt(SlabValue, Level)
        AreaValue = sum(LoopArea(LoopValue) for LoopValue in Loops)
        Plane = dict(x=0.0, y=0.0, xx=0.0, yy=0.0, xy=0.0)
        for LoopValue in Loops:
            for KeyValue, Value in PlaneMoments(LoopPolygon(LoopValue, 4096)).items():
                Plane[KeyValue] += Value
        MassValue["volume"] += AreaValue * Scale
        MassValue["z"] += AreaValue * Level * Scale
        MassValue["zz"] += AreaValue * Level * Level * Scale
        MassValue["xz"] += Plane["x"] * Level * Scale
        MassValue["yz"] += Plane["y"] * Level * Scale
        for KeyValue in ("x", "y", "xx", "yy", "xy"):
            MassValue[KeyValue] += Plane[KeyValue] * Scale


def PrismMass(Solid: PrismSolid) -> dict[str, float]:
    MassValue = dict(
        volume=0.0, x=0.0, y=0.0, z=0.0, xx=0.0, yy=0.0, zz=0.0, xy=0.0, xz=0.0, yz=0.0
    )
    for SlabValue in Solid.Slabs:
        if SlabValue.RoofLoops:
            TaperMassMut(MassValue, SlabValue)
            continue
        Lower, Upper = SlabValue.LowerCm, SlabValue.UpperCm
        Height = Upper - Lower
        AreaValue = sum(LoopArea(LoopValue) for LoopValue in SlabValue.Loops)
        Plane = dict(x=0.0, y=0.0, xx=0.0, yy=0.0, xy=0.0)
        for LoopValue in SlabValue.Loops:
            for KeyValue, Value in PlaneMoments(LoopPolygon(LoopValue, 4096)).items():
                Plane[KeyValue] += Value
        Linear, Square = (Upper * Upper - Lower * Lower) / 2.0, (
            Upper**3 - Lower**3
        ) / 3.0
        MassValue["volume"] += AreaValue * Height
        MassValue["z"] += AreaValue * Linear
        MassValue["zz"] += AreaValue * Square
        MassValue["xz"] += Plane["x"] * Linear
        MassValue["yz"] += Plane["y"] * Linear
        for KeyValue in ("x", "y", "xx", "yy", "xy"):
            MassValue[KeyValue] += Plane[KeyValue] * Height
    MassValue["area"] = SolidArea(Solid)
    return MassValue


def SolidMass(Solid: PrismSolid) -> dict[str, float]:
    if not Solid.Rounds:
        return PrismMass(Solid)
    Plain = ReplaceValue(Solid, Rounds=())
    Delta = ApplyRounds(BuildShape(Plain), Solid.Rounds)[1]
    return {
        KeyValue: Value + Delta.get(KeyValue, 0.0)
        for KeyValue, Value in PrismMass(Plain).items()
    }


def LineSpread(Lower: LineSpan, Upper: LineSpan) -> float:
    HeadX, HeadY = SpanHeading(Lower, False)
    DeltaX = Upper.StartCm[0] - Lower.StartCm[0]
    DeltaY = Upper.StartCm[1] - Lower.StartCm[1]
    return DeltaX * HeadY - DeltaY * HeadX


def WallArea(FaceValue: WallFace) -> float:
    Height = FaceValue.UpperCm - FaceValue.LowerCm
    RoofSpan = FaceValue.RoofSpan
    if RoofSpan is None:
        return sum(
            SpanLength(UseValue.Edge.Span)
            * UseValue.Edge.LevelCm
            * (-1.0 if UseValue.Forward else 1.0)
            for LoopValue in FaceValue.Loops
            for UseValue in LoopValue
            if isinstance(UseValue.Edge, LevelEdge)
        )
    Lengths = (SpanLength(FaceValue.Span), SpanLength(RoofSpan))
    Growth = (Lengths[1] - Lengths[0]) / KFullTurn
    if isinstance(RoofSpan, LineSpan) and isinstance(FaceValue.Span, LineSpan):
        Growth = LineSpread(FaceValue.Span, RoofSpan)
    return (Lengths[0] + Lengths[1]) / 2.0 * Hypotenuse(Height, Growth)


def SolidArea(Solid: PrismSolid) -> float:
    Total = 0.0
    for FaceValue in BuildShape(Solid).Faces:
        if isinstance(FaceValue, WallFace):
            Total += WallArea(FaceValue)
            continue
        if not isinstance(FaceValue, CapFace):
            raise ValueError("Fusion rounded faces need the round mass sum")
        Signed = 0.0
        for LoopValue in FaceValue.Loops:
            for UseValue in LoopValue:
                if isinstance(UseValue.Edge, LevelEdge):
                    Amount = SpanArea(UseValue.Edge.Span)
                    Signed += Amount if UseValue.Forward else -Amount
        Total += abs(Signed)
    return Total
