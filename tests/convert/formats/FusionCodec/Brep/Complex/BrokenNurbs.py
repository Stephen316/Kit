from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
    NurbsFace,
    NurbsUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.PatchSheet import (
    LinePcurve,
    PatchSheet,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from tests.convert.formats.FusionCodec.Brep.Complex.NurbsSamples import (
    BicubicPatch,
    PillowBody,
    RationalPatch,
)

KNurbsFaults = (
    "knots",
    "poles",
    "weights",
    "rational",
    "range",
    "surface",
    "vertex",
    "orphan",
    "sense",
)


def SwapSurface(Model: NurbsBody, Surface: BsSurface) -> NurbsBody:
    return ReplaceValue(Model, Faces=(ReplaceValue(Model.Faces[0], Surface=Surface),))


def FirstSurface(Model: NurbsBody) -> BsSurface:
    Surface = Model.Faces[0].Surface
    assert isinstance(Surface, BsSurface)
    return Surface


def SwapLeadUse(Model: NurbsBody, UseSpec: NurbsUse) -> NurbsBody:
    FaceSpec = Model.Faces[0]
    Edited = NurbsFace(FaceSpec.Surface, (UseSpec, *FaceSpec.Uses[1:]))
    return ReplaceValue(Model, Faces=(Edited, *Model.Faces[1:]))


def BrokenNurbs(Fault: str) -> NurbsBody:
    Sheet = PatchSheet(BicubicPatch())
    Surface = FirstSurface(Sheet)
    LeadUse = Sheet.Faces[0].Uses[0]
    if Fault == "knots":
        return SwapSurface(Sheet, ReplaceValue(Surface, UKnots=(0.0, 1.0, 0.4)))
    if Fault == "poles":
        return SwapSurface(Sheet, ReplaceValue(Surface, Poles=Surface.Poles[:-1]))
    if Fault == "weights":
        Rational = PatchSheet(RationalPatch())
        Weighted = FirstSurface(Rational)
        return SwapSurface(
            Rational, ReplaceValue(Weighted, Weights=(0.0, *Weighted.Weights[1:]))
        )
    if Fault == "rational":
        Rational = PatchSheet(RationalPatch())
        return SwapSurface(
            Rational,
            ReplaceValue(FirstSurface(Rational), Rational=False, RationalForm=""),
        )
    if Fault == "range":
        return SwapLeadUse(
            Sheet,
            ReplaceValue(LeadUse, Pcurve=LinePcurve((0.0, 0.0), (1.0, 0.0), 0.0, 2.0)),
        )
    if Fault == "surface":
        return SwapLeadUse(
            Sheet,
            ReplaceValue(LeadUse, Pcurve=LinePcurve((0.0, 0.1), (1.0, 0.1), 0.0, 1.0)),
        )
    if Fault == "vertex":
        Moved = (Sheet.PointsCm[0][0], Sheet.PointsCm[0][1], Sheet.PointsCm[0][2] + 0.5)
        return ReplaceValue(Sheet, PointsCm=(Moved, *Sheet.PointsCm[1:]))
    if Fault == "orphan":
        return ReplaceValue(Sheet, PointsCm=(*Sheet.PointsCm, (9.0, 9.0, 9.0)))
    if Fault == "sense":
        Pillow = PillowBody()
        Flipped = Pillow.Faces[0].Uses[0]
        return SwapLeadUse(Pillow, ReplaceValue(Flipped, Reversed=not Flipped.Reversed))
    raise ValueError("Unknown NURBS fault sample")
