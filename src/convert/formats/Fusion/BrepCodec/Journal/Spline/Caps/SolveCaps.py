from dataclasses import replace as ReplaceFields
from fractions import Fraction
from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CapKnots import (
    KClamp,
    KKnotTuple,
    ExpandKnots,
    KnotRatio,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CapLayout import (
    KSpan,
    KCapRow,
    CapLayout,
    CapKeys,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CreaseRows import (
    KDartValence,
    CreaseRows,
    CreaseSpoke,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.DartRows import (
    DartHidden,
    DartRows,
    DartSpoke,
    IsDart,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.HardRows import HardRows
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.LeastSolve import (
    SolveLeast,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.RingRows import (
    RingRows,
    TangentRows,
    TwistRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.WindowRows import (
    WindowRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import (
    KCapKey,
    CapInput,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)

KPolarSteps = ((2.0, 2), (-2.0, 3), (1.0, 4))


def PolarPole(
    Reference: KMapping[KCapKey, KPoleRow], CapKey: KCapKey
) -> KPoleRow | None:
    Found = Reference.get(CapKey)
    if Found is not None or CapKey == ("ep",):
        return Found
    Parts: list[tuple[float, KPoleRow]] = []
    for Scalar, Index in KPolarSteps:
        if CapKey[0] == "spoke":
            Other: KCapKey = ("spoke", CapKey[1], Index)
        elif CapKey[2] == 1:
            Other = ("in", CapKey[1], Index, CapKey[3])
        else:
            Other = ("in", CapKey[1], CapKey[2], Index)
        RowValue = Reference.get(Other)
        if RowValue is None:
            return None
        Parts.append((Scalar, RowValue))
    return MixRows(Parts)


def MakeLayout(
    Request: CapInput, Limit: KPoleRow, CapList: tuple[KCapKey, ...]
) -> CapLayout:
    if len(Request.Sectors) != Request.Valence:
        raise ValueError("Fusion Form cap rule found a sector count off the valence")
    KnotsI = tuple(ExpandKnots(Sector.KnotsI) for Sector in Request.Sectors)
    KnotsJ = tuple(ExpandKnots(Sector.KnotsJ) for Sector in Request.Sectors)
    if len({Knots[KClamp] for Knots in KnotsI + KnotsJ}) != 1:
        raise ValueError("Fusion Form cap rule found sectors with different h")
    Netref: list[KPoleRow] = []
    for CapKey in CapList:
        RowValue = Limit if CapKey == ("ep",) else PolarPole(Request.Reference, CapKey)
        if RowValue is None:
            raise ValueError("Fusion Form cap rule has no net pole " + str(CapKey))
        Netref.append(RowValue)
    return CapLayout(
        Request.Valence,
        KnotsI,
        KnotsJ,
        {CapKey: SlotIndex for SlotIndex, CapKey in enumerate(CapList)},
        Request.Reference,
        tuple(Netref),
    )


def SpokeRatios(
    Valence: int, KnotsI: tuple[KKnotTuple, ...], KnotsJ: tuple[KKnotTuple, ...]
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    RatiosI = tuple(KnotRatio(Knots) for Knots in KnotsI)
    RatiosJ = tuple(KnotRatio(Knots) for Knots in KnotsJ)
    for Spoke in range(Valence):
        if RatiosI[Spoke] != RatiosJ[(Spoke - 1) % Valence]:
            raise ValueError(
                "Fusion Form cap rule found a spoke whose sides see different spans"
            )
    return RatiosI, RatiosJ


def ScaleRows(
    RowList: list[KCapRow], Grips: list[int]
) -> tuple[list[list[float]], list[list[float]]]:
    Matrix: list[list[float]] = []
    Sides: list[list[float]] = []
    for Dense, SideRow in RowList:
        Scale = max(abs(Value) for Value in Dense)
        if Scale == 0.0:
            continue
        Matrix.append([Value / Scale for Value in Dense])
        Sides.append([SideRow.get(GripIndex, 0.0) / Scale for GripIndex in Grips])
    return Matrix, Sides


def DartReference(
    Reference: KMapping[KCapKey, KPoleRow], Spoke: int
) -> dict[KCapKey, KPoleRow]:
    Found = dict(Reference)
    for Upper in (Spoke + 1, Spoke - 1):
        Wrapped = Upper % KDartValence
        Before = (Upper - 1) % KDartValence
        for Index in range(1, KSpan):
            Lower = PolarPole(Reference, ("in", Wrapped, Index, 1))
            Higher = PolarPole(Reference, ("in", Before, 1, Index))
            if Lower is not None and Higher is not None:
                Found[("spoke", Wrapped, Index)] = MixRows(
                    ((0.5, Lower), (0.5, Higher))
                )
    return Found


def CapRowList(Request: CapInput, Layout: CapLayout, Limit: KPoleRow) -> list[KCapRow]:
    Ratios = SpokeRatios(Request.Valence, Layout.KnotsI, Layout.KnotsJ)
    if IsDart(Request.Creased):
        return DartRows(Layout, Limit, Ratios, DartSpoke(Request.Creased))
    if any(Request.Creased):
        return CreaseRows(Layout, Limit, Ratios, Request.Creased)
    return [
        *HardRows(Layout, Limit),
        *WindowRows(Layout, *Ratios),
        *RingRows(Layout, Limit, Ratios[0]),
        *TangentRows(Layout, Ratios[0]),
        *TwistRows(Layout),
    ]


def SolveCaps(Request: CapInput) -> dict[KCapKey, KPoleRow]:
    DartCap = IsDart(Request.Creased)
    if any(Request.Creased) and not DartCap:
        _ = CreaseSpoke(Request.Creased)
    Limit = Request.Limit
    if Limit is None:
        raise ValueError("Fusion Form cap rule has no limit row")
    CapList = CapKeys(Request.Valence)
    Hidden: frozenset[KCapKey] = (
        DartHidden(DartSpoke(Request.Creased)) if DartCap else frozenset()
    )
    if Request.Unknown != frozenset(CapList) - Hidden:
        raise ValueError("Fusion Form cap rule expects the cap keys within four spans")
    Completed = (
        ReplaceFields(
            Request,
            Reference=DartReference(Request.Reference, DartSpoke(Request.Creased)),
        )
        if DartCap
        else Request
    )
    Layout = MakeLayout(Completed, Limit, CapList)
    RowList = CapRowList(Completed, Layout, Limit)
    Grips = sorted({GripIndex for _, SideRow in RowList for GripIndex in SideRow})
    Matrix, Sides = ScaleRows(RowList, Grips)
    Solution = SolveLeast(Matrix, Sides)
    return {
        CapKey: {
            GripIndex: Value
            for GripIndex, Value in zip(Grips, Solution[SlotIndex])
            if Value != 0.0
        }
        for CapKey, SlotIndex in Layout.Slots.items()
        if CapKey in Request.Unknown
    }
