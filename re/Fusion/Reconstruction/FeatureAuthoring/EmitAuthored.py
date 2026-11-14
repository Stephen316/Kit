"""Emit Kit-authored feature documents that mirror the native controls.

Run with Python 3.14 (ZIP method 93) from the repository root:
    /opt/homebrew/bin/python3.14 -I re/Fusion/Reconstruction/FeatureAuthoring/EmitAuthored.py [Case ...]

Cuboid cases start from the CaptureControls.py base part: a 40 x 30 mm
rectangle at the origin extruded 20 mm through the cuboid writer. Part cases
author every body from independent sketch profiles through ExtrudeSpec.
Every dimension matches its native control so the acceptance run can compare
geometry directly. Passing case names emits only those cases and merges them
into the existing manifest.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.dont_write_bytecode = True

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import ChamferSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import CircleCurve  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import ExtrudeSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import FilletSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import LineCurve  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import PatternSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import CircularSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import MirrorSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import OffsetSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import RevolveSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import CombineSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import BodyGridSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import BodyRingSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import SweepSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import PasteSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SolidMass import SolidMass  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import BuildShape  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart  # noqa: E402

OUTPUT = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Authored"


def rect(x0, y0, x1, y1):
    return (
        LineCurve((x0, y0), (x1, y0)),
        LineCurve((x1, y0), (x1, y1)),
        LineCurve((x1, y1), (x0, y1)),
        LineCurve((x0, y1), (x0, y0)),
    )


def slot(x0, y0, x1, r):
    return (
        LineCurve((x0, y0 - r), (x1, y0 - r)),
        ArcCurve((x1, y0), r, -90.0, 180.0),
        LineCurve((x1, y0 + r), (x0, y0 + r)),
        ArcCurve((x0, y0), r, 90.0, 180.0),
    )


CONCAVE = (
    LineCurve((0, 0), (40, 0)),
    LineCurve((40, 0), (40, 30)),
    LineCurve((40, 30), (30, 30)),
    ArcCurve((20, 30), 10, 180.0, 180.0),
    LineCurve((10, 30), (0, 30)),
    LineCurve((0, 30), (0, 0)),
)


def base(name="Base extrude", extent="one", against=0.0):
    return ExtrudeSpec(rect(0, 0, 40, 30), 20.0, "new", extent, against, "Base sketch", name)


POCKET = ExtrudeSpec((CircleCurve((8, 8), 3),), 20.0, "cut", "one", 0.0, "Pocket sketch", "Pocket extrude")


def hole(radius, distance, operation, name, extent="one"):
    return ExtrudeSpec((CircleCurve((20, 15), radius),), distance, operation, extent, 0.0, name + " sketch", name)


CUBOID = {
    "Fillet": (FilletSpec((40.0, 30.0), 3.0),),
    "Chamfer": (ChamferSpec((40.0, 30.0), 3.0),),
    "Shell": (ShellSpec(2.0),),
    "FilletShell": (FilletSpec((40.0, 30.0), 3.0), ShellSpec(2.0)),
    "ShellOpenSide": (ShellSpec(2.0, "Open shell", SidesMm=((20.0, 0.0),)),),
    "ShellOpenCorner": (ShellSpec(2.0, "Open corner", SidesMm=((20.0, 0.0), (40.0, 15.0))),),
    "MultiFeature": (
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        ChamferSpec((0.0, 0.0), 3.0, "Corner Bevel"),
        FilletSpec((40.0, 0.0), 4.0),
        ShellSpec(2.0, "Hollow"),
    ),
}

PART = {
    "ExtrudeNew": (base(),),
    "ExtrudeSymmetric": (base(extent="symmetric"),),
    "ExtrudeTwoSided": (base(extent="two", against=5.0),),
    "ExtrudeFlip": (base(extent="flip"),),
    "ProfileSlot": (ExtrudeSpec(slot(10, 10, 30, 10), 20.0, "new", "one", 0.0, "Slot sketch", "Slot extrude"),),
    "ProfileConcave": (ExtrudeSpec(CONCAVE, 20.0, "new", "one", 0.0, "Notch sketch", "Notch extrude"),),
    "ProfileCircle": (ExtrudeSpec((CircleCurve((20, 15), 10),), 20.0, "new", "one", 0.0, "Disc sketch", "Disc extrude"),),
    "ExtrudeJoin": (base(), hole(5, 30, "join", "Boss")),
    "ExtrudeCut": (base(), hole(5, 20, "cut", "Hole")),
    "ExtrudeIntersect": (base(), hole(10, 20, "intersect", "Core")),
    "ExtrudeBlindCut": (base(), hole(5, 10, "cut", "Pocket")),
    "ExtrudeSlotCut": (base(), ExtrudeSpec(slot(15, 15, 25, 5), 20.0, "cut", "one", 0.0, "Slot sketch", "Slot extrude")),
    "ExtrudeSymmetricCut": (base(), hole(5, 20, "cut", "Pocket", "symmetric")),
    "PartCutFillet": (
        base(),
        ExtrudeSpec(slot(15, 15, 25, 5), 20.0, "cut", "one", 0.0, "Slot sketch", "Slot extrude"),
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        ChamferSpec((0.0, 0.0), 2.0, "Corner Bevel"),
    ),
    "PartConcaveShell": (
        ExtrudeSpec(CONCAVE, 20.0, "new", "one", 0.0, "Notch sketch", "Notch extrude"),
        FilletSpec((40.0, 0.0), 4.0, "Corner Round"),
        ShellSpec(2.0, "Hollow"),
    ),
    "HoleFlat": (base(), HoleSpec((20.0, 15.0), 8.0, 10.0, FeatureName="Top hole")),
    "HoleThrough": (base(), HoleSpec((20.0, 15.0), 8.0, FeatureName="Top hole")),
    "HoleCounterboreFlat": (base(), HoleSpec((20.0, 15.0), 6.0, 10.0, 10.0, 4.0, "Top hole")),
    "HoleCounterbore": (base(), HoleSpec((20.0, 15.0), 6.0, 0.0, 10.0, 4.0, "Top hole")),
    "HoleCountersink": (base(), HoleSpec((20.0, 15.0), 6.0, FeatureName="Top hole", SinkDiameterMm=10.0)),
    "HoleCountersinkFlat": (base(), HoleSpec((20.0, 15.0), 6.0, 10.0, FeatureName="Top hole", SinkDiameterMm=12.0, SinkAngleDegrees=82.0)),
    "RectPattern": (base(), POCKET, PatternSpec(1, 3, 12.0, 2, 14.0, "Pocket grid")),
    "FeatureCircPattern": (base(), POCKET, CircularSpec(1, 2, 40.0, "Pocket arc")),
    "MirrorFeature": (base(), POCKET, PlaneSpec(20.0, "yz", "Mid plane"), MirrorSpec(1, 2, "Pocket mirror")),
    "PlaneOffset": (base(), PlaneSpec(15.0, "xy", "Offset plane")),
    "HoleGrid": (base(), HoleSpec((8.0, 8.0), 5.0, 10.0, FeatureName="Corner hole"), PatternSpec(1, 3, 12.0, 2, 14.0, "Hole grid")),
    "MultiPocketPart": (
        base(),
        ExtrudeSpec(slot(10, 22, 14, 3), 8.0, "cut", "one", 0.0, "Slot sketch", "Slot pocket"),
        HoleSpec((8.0, 8.0), 4.0, FeatureName="Corner hole"),
        PatternSpec(2, 2, 12.0, 1, 10.0, "Hole row"),
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        PlaneSpec(20.0, "yz", "Mid plane"),
        MirrorSpec(1, 5, "Slot mirror"),
    ),
    "MultiDiscPart": (
        ExtrudeSpec((CircleCurve((0, 0), 20),), 12.0, "new", "one", 0.0, "Disc sketch", "Disc extrude"),
        ExtrudeSpec((CircleCurve((12, 0), 3),), 6.0, "cut", "one", 0.0, "Pocket sketch", "Pocket extrude"),
        CircularSpec(1, 4, 360.0, "Pocket ring"),
        HoleSpec((0.0, 0.0), 8.0, 0.0, 14.0, 4.0, "Center bore"),
    ),
    "ChamferTwoDistances": (base(), ChamferSpec((40.0, 30.0), 3.0, "Corner bevel", 2.0)),
    "ChamferDistanceAngle": (base(), ChamferSpec((40.0, 30.0), 3.0, "Corner bevel", 0.0, 30.0)),
    "FilletTwoEdges": (base(), FilletSpec((40.0, 30.0), 3.0, "Corner rounds", ((0.0, 0.0),))),
    "ChamferTwoEdges": (base(), ChamferSpec((40.0, 30.0), 3.0, "Corner bevels", MoreCornersMm=((0.0, 0.0),))),
    "CornerSetPart": (
        base(),
        HoleSpec((30.0, 10.0), 6.0, FeatureName="Side hole"),
        FilletSpec((40.0, 30.0), 4.0, "Corner rounds", ((0.0, 0.0),)),
        ChamferSpec((40.0, 0.0), 3.0, "Corner bevel", 0.0, 30.0),
    ),
    "ConstructionSet": (
        base(),
        PlaneSpec(15.0, "xy", "Offset plane"),
        AxisSpec((40.0, 30.0), "Edge axis"),
        PointSpec((40.0, 30.0), "Corner point"),
    ),
    "ConstructionPart": (
        base(),
        POCKET,
        AxisSpec((0.0, 0.0), "Corner axis"),
        PointSpec((40.0, 0.0), "Corner point"),
        FilletSpec((40.0, 30.0), 3.0, "Corner round"),
    ),
}

DISC = ExtrudeSpec((CircleCurve((0, 0), 25),), 10.0, "new", "one", 0.0, "Disc sketch", "Disc extrude")

PART.update({
    "RevolveFull": (RevolveSpec(10.0, 20.0, 0.0, 30.0, 360.0, "new", "Revolve sketch", "Tube revolve"),),
    "RevolveHalf": (RevolveSpec(10.0, 20.0, 0.0, 30.0, 180.0, "new", "Revolve sketch", "Tube revolve"),),
    "RevolveJoin": (DISC, RevolveSpec(10.0, 15.0, 10.0, 20.0, 360.0, "join", "Ring sketch", "Ring revolve")),
    "RevolveCut": (DISC, RevolveSpec(15.0, 22.0, 6.0, 10.0, 90.0, "cut", "Groove sketch", "Groove revolve")),
})
PART.update({
    "MoveTurnPart": (base(), MoveSpec((5.0, 5.0, 2.0), "Body turn", 30.0), FilletSpec((24.64101615137754, 50.98076211353316), 3.0, "Turned round")),
})
CUBOID["MoveBody"] = (MoveSpec((10.0, 0.0, 0.0), "Body move"),)
PART.update({
    "OffsetTop": (base(), OffsetSpec(5.0, "Top offset")),
    "OffsetTopTrim": (base(), OffsetSpec(-5.0, "Top trim")),
    "OffsetSide": (base(), OffsetSpec(4.0, "Side offset", (40.0, 15.0))),
    "OffsetRoundFront": (base(), FilletSpec((40.0, 30.0), 3.0, "Corner round"), OffsetSpec(4.0, "Front offset", (20.0, 0.0))),
})
PART.update({
    "DraftSides": (base(), DraftSpec(5.0, "Side draft")),
    "DraftInward": (base(), DraftSpec(-5.0, "Side taper")),
    "DraftCutPart": (base(), ChamferSpec((40.0, 30.0), 3.0, FeatureName="Corner cut"), DraftSpec(5.0, "Side draft")),
})
POST = ExtrudeSpec((CircleCurve((40, 30), 10),), 20.0, "new", "one", 0.0, "Post sketch", "Post extrude")
CUBE = ExtrudeSpec(rect(0, 0, 10, 10), 10.0, "new", "one", 0.0, "Cube sketch", "Cube extrude")
RING_CUBE = ExtrudeSpec(rect(20, -5, 30, 5), 10.0, "new", "one", 0.0, "Cube sketch", "Cube extrude")
PART.update({
    "ExtrudeSecondBody": (base(), ExtrudeSpec((CircleCurve((60, 15), 5),), 20.0, "new", "one", 0.0, "Post sketch", "Post extrude")),
    "RevolveBody": (base(), RevolveSpec(60.0, 80.0, 0.0, 10.0, 360.0, "new", "Ring sketch", "Ring revolve")),
    "CombineJoin": (base(), POST, CombineSpec(1, (2,), "join", False, "Body combine")),
    "CombineCut": (base(), POST, CombineSpec(1, (2,), "cut", False, "Body combine")),
    "CombineIntersect": (base(), POST, CombineSpec(1, (2,), "intersect", False, "Body combine")),
    "CombineKeep": (base(), POST, CombineSpec(1, (2,), "join", True, "Body combine")),
    "SplitYZ": (base(), PlaneSpec(20.0, "yz", "Split plane"), SplitSpec(1, 1, "Body split")),
    "SplitXZ": (base(), PlaneSpec(10.0, "xz", "Split plane"), SplitSpec(1, 1, "Body split")),
    "SplitXY": (base(), PlaneSpec(8.0, "xy", "Split plane"), SplitSpec(1, 1, "Body split")),
    "BodyRectPattern": (CUBE, BodyGridSpec(1, 3, 15.0, 2, 20.0, "Cube grid")),
    "BodyCircPattern": (RING_CUBE, BodyRingSpec(1, 4, 360.0, "Cube ring")),
})
PART.update({
    "LoftRects": (LoftSpec(rect(0, 0, 40, 30), rect(10, 10, 30, 20), 30.0, FeatureName="Block loft"),),
    "LoftCircles": (LoftSpec((CircleCurve((0, 0), 10),), (CircleCurve((0, 0), 5),), 30.0, FeatureName="Cone loft"),),
    "LoftWedgeBody": (base(), LoftSpec(rect(50, 0, 90, 30), rect(55, 20, 75, 25), 25.0, "Wedge base", "Wedge plane", "Wedge top", "Wedge loft")),
})
BEND = (LineCurve((0, 0), (0, 20)), ArcCurve((-30, 20), 30, 0, 90))
S_CURVE = (LineCurve((0, 0), (0, 10)), ArcCurve((20, 10), 20, 180, -90), ArcCurve((20, 50), 20, -90, 90))
PART.update({
    "SweepBend": (SweepSpec(BEND, -5.0, 5.0, 0.0, 10.0, FeatureName="Bend sweep"),),
    "SweepHook": (SweepSpec((*BEND, LineCurve((-30, 50), (-50, 50))), -5.0, 5.0, 0.0, 10.0, FeatureName="Bend sweep"),),
    "SweepSCurve": (SweepSpec(S_CURVE, -3.0, 5.0, 2.0, 8.0, "Bar profile", "Bar path", "Bar sweep"),),
    "SweepSecondBody": (base(), SweepSpec(BEND, -15.0, -5.0, 0.0, 10.0, "Rail profile", "Rail path", "Rail sweep")),
})
SIDE_POST = ExtrudeSpec((CircleCurve((60, 15), 5),), 20.0, "new", "one", 0.0, "Post sketch", "Post extrude")
PART.update({
    "PastePlain": (base(), PasteSpec(1, "Body paste")),
    "PasteFillet": (base(), FilletSpec((40.0, 30.0), 3.0, "Corner round"), PasteSpec(1, "Body paste")),
    "PasteTwice": (base(), PasteSpec(1, "First paste"), PasteSpec(1, "Second paste")),
    "PasteSecond": (base(), SIDE_POST, PasteSpec(2, "Post paste")),
    "PastePocket": (base(), POCKET, PasteSpec(1, "Body paste")),
    "PasteCombine": (base(), POST, PasteSpec(2, "Post paste"), CombineSpec(1, (3,), "cut", False, "Body combine")),
})

CASES = {**CUBOID, **PART}

EDITS = {
    "Fillet": [{"feature": "Fillet", "expression": "4 mm"}],
    "Chamfer": [{"feature": "Chamfer", "expression": "2 mm"}],
    "Shell": [{"feature": "Shell", "expression": "3 mm"}],
    "FilletShell": [{"feature": "Shell", "expression": "1.5 mm"}, {"feature": "height", "expression": "25 mm"}],
    "ShellOpenSide": [{"feature": "Open shell", "expression": "3 mm"}, {"feature": "height", "expression": "25 mm"}],
    "ShellOpenCorner": [{"feature": "Open corner", "expression": "4 mm"}, {"feature": "height", "expression": "15 mm"}],
    "MultiFeature": [{"feature": "Corner Round", "expression": "5 mm"}, {"feature": "height", "expression": "25 mm"}],
    "ExtrudeNew": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "ExtrudeSymmetric": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "16 mm"}],
    "ExtrudeTwoSided": [{"feature": "Base extrude", "role": "AgainstDistance", "expression": "8 mm"}],
    "ExtrudeFlip": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "-12 mm"}],
    "ProfileSlot": [{"feature": "Slot extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "ProfileConcave": [{"feature": "Notch extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "ProfileCircle": [{"feature": "Disc extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "ExtrudeJoin": [{"feature": "Boss", "role": "AlongDistance", "expression": "35 mm"}],
    "ExtrudeCut": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "ExtrudeIntersect": [{"feature": "Core", "role": "AlongDistance", "expression": "15 mm"}],
    "ExtrudeBlindCut": [{"feature": "Pocket", "role": "AlongDistance", "expression": "6 mm"}],
    "ExtrudeSlotCut": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "ExtrudeSymmetricCut": [{"feature": "Pocket", "role": "AlongDistance", "expression": "12 mm"}],
    "PartCutFillet": [{"feature": "Corner Round", "expression": "4 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "PartConcaveShell": [{"feature": "Hollow", "expression": "1.5 mm"}, {"feature": "Notch extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleFlat": [{"feature": "Top hole", "role": "HoleDiameter", "expression": "6 mm"}, {"feature": "Top hole", "role": "HoleDepth", "expression": "12 mm"}],
    "HoleThrough": [{"feature": "Top hole", "role": "HoleDiameter", "expression": "10 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleCounterboreFlat": [{"feature": "Top hole", "role": "CBDiameter", "expression": "12 mm"}, {"feature": "Top hole", "role": "CBDepth", "expression": "3 mm"}],
    "HoleCounterbore": [{"feature": "Top hole", "role": "HoleDiameter", "expression": "5 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleCountersink": [{"feature": "Top hole", "role": "CSDiameter", "expression": "12 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleCountersinkFlat": [{"feature": "Top hole", "role": "CSAngle", "expression": "100 deg"}, {"feature": "Top hole", "role": "HoleDepth", "expression": "14 mm"}],
    "RectPattern": [{"feature": "Pocket grid", "role": "uSpaceDistance", "expression": "11 mm"}, {"feature": "Pocket grid", "role": "CountV", "expression": "1"}],
    "FeatureCircPattern": [{"feature": "Pocket arc", "role": "TotalAngle", "expression": "30 deg"}],
    "MirrorFeature": [{"feature": "Mid plane", "role": "AlongDistance", "expression": "18 mm"}],
    "PlaneOffset": [{"feature": "Offset plane", "role": "AlongDistance", "expression": "12 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleGrid": [{"feature": "Hole grid", "role": "vSpaceDistance", "expression": "12 mm"}, {"feature": "Corner hole", "role": "HoleDepth", "expression": "8 mm"}],
    "MultiPocketPart": [{"feature": "Hole row", "role": "uSpaceDistance", "expression": "10 mm"}, {"feature": "Corner Round", "expression": "4 mm"}, {"feature": "Mid plane", "role": "AlongDistance", "expression": "21 mm"}],
    "MultiDiscPart": [{"feature": "Pocket ring", "role": "countU", "expression": "6"}, {"feature": "Center bore", "role": "CBDiameter", "expression": "16 mm"}],
    "ChamferTwoDistances": [{"feature": "Corner bevel", "role": "Distance 2", "expression": "1 mm"}],
    "ChamferDistanceAngle": [{"feature": "Corner bevel", "role": "Rotate Angle", "expression": "40 deg"}],
    "FilletTwoEdges": [{"feature": "Corner rounds", "expression": "4 mm"}],
    "ChamferTwoEdges": [{"feature": "Corner bevels", "expression": "2 mm"}],
    "CornerSetPart": [{"feature": "Corner rounds", "expression": "5 mm"}, {"feature": "Corner bevel", "role": "Rotate Angle", "expression": "45 deg"}, {"feature": "Side hole", "role": "HoleDiameter", "expression": "8 mm"}],
    "ConstructionSet": [{"feature": "Offset plane", "role": "AlongDistance", "expression": "12 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "ConstructionPart": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "26 mm"}, {"feature": "Corner round", "expression": "4 mm"}],
    "RevolveFull": [{"feature": "Tube revolve", "role": "AlongAngle", "expression": "270 deg"}],
    "RevolveHalf": [{"feature": "Tube revolve", "role": "AlongAngle", "expression": "120 deg"}],
    "RevolveJoin": [{"feature": "Ring revolve", "role": "AlongAngle", "expression": "180 deg"}, {"feature": "Disc extrude", "role": "AlongDistance", "expression": "12 mm"}],
    "RevolveCut": [{"feature": "Groove revolve", "role": "AlongAngle", "expression": "120 deg"}],
    "MoveBody": [{"feature": "height", "expression": "25 mm"}],
    "MoveTurnPart": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}, {"feature": "Turned round", "expression": "4 mm"}],
    "OffsetTop": [{"feature": "Top offset", "role": "distance", "expression": "8 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "OffsetTopTrim": [{"feature": "Top trim", "role": "distance", "expression": "-8 mm"}],
    "OffsetSide": [{"feature": "Side offset", "role": "distance", "expression": "6 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "OffsetRoundFront": [{"feature": "Front offset", "role": "distance", "expression": "-5 mm"}, {"feature": "Corner round", "expression": "4 mm"}],
    "DraftSides": [{"feature": "Side draft", "role": "Angle1", "expression": "8 deg"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "DraftInward": [{"feature": "Side taper", "role": "Angle1", "expression": "-3 deg"}],
    "DraftCutPart": [{"feature": "Side draft", "role": "Angle1", "expression": "3 deg"}, {"feature": "Corner cut", "expression": "4 mm"}],
    "ExtrudeSecondBody": [{"feature": "Post extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "RevolveBody": [{"feature": "Ring revolve", "role": "AlongAngle", "expression": "180 deg"}],
    "CombineJoin": [{"feature": "Post extrude", "role": "AlongDistance", "expression": "30 mm"}],
    "CombineCut": [{"feature": "Post extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "CombineIntersect": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "CombineKeep": [{"feature": "Post extrude", "role": "AlongDistance", "expression": "30 mm"}],
    "SplitYZ": [{"feature": "Split plane", "role": "AlongDistance", "expression": "25 mm"}],
    "SplitXZ": [{"feature": "Split plane", "role": "AlongDistance", "expression": "20 mm"}],
    "SplitXY": [{"feature": "Split plane", "role": "AlongDistance", "expression": "12 mm"}],
    "BodyRectPattern": [{"feature": "Cube grid", "role": "uSpaceDistance", "expression": "18 mm"}, {"feature": "Cube grid", "role": "CountV", "expression": "3"}],
    "BodyCircPattern": [{"feature": "Cube ring", "role": "countU", "expression": "6"}],
    "LoftRects": [{"feature": "Loft plane", "role": "AlongDistance", "expression": "40 mm"}],
    "LoftCircles": [{"feature": "Loft plane", "role": "AlongDistance", "expression": "20 mm"}],
    "LoftWedgeBody": [{"feature": "Wedge plane", "role": "AlongDistance", "expression": "30 mm"}],
    "SweepBend": [{"feature": "Bend sweep", "role": "AlongDistance", "expression": "0.5"}],
    "SweepHook": [{"feature": "Bend sweep", "role": "AlongDistance", "expression": "0.75"}],
    "SweepSCurve": [{"feature": "Bar sweep", "role": "AlongDistance", "expression": "0.5"}],
    "SweepSecondBody": [{"feature": "Rail sweep", "role": "AlongDistance", "expression": "0.5"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "PastePlain": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "PasteFillet": [{"feature": "Corner round", "expression": "4 mm"}],
    "PasteTwice": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "PasteSecond": [{"feature": "Post extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "PastePocket": [{"feature": "Pocket extrude", "role": "AlongDistance", "expression": "10 mm"}],
    "PasteCombine": [{"feature": "Post extrude", "role": "AlongDistance", "expression": "30 mm"}],
}


CORNER_ROUNDS = FilletSpec((40.0, 30.0), 5.0, "Corner rounds", ((0.0, 0.0), (40.0, 0.0), (0.0, 30.0)))
ROUND_DISC = ExtrudeSpec((CircleCurve((0, 0), 10),), 20.0, "new", "one", 0.0, "Disc sketch", "Disc extrude")
SLOT_BAR = ExtrudeSpec(slot(10, 15, 30, 8), 20.0, "new", "one", 0.0, "Slot sketch", "Slot extrude")
STEP_POINTS = ((0.0, 0.0), (40.0, 0.0), (40.0, 15.0), (20.0, 15.0), (20.0, 30.0), (0.0, 30.0))
STEP_BAR = ExtrudeSpec(tuple(LineCurve(a, b) for a, b in zip(STEP_POINTS, STEP_POINTS[1:] + STEP_POINTS[:1])), 20.0, "new", "one", 0.0, "Step sketch", "Step extrude")
SQUARE_POST = ExtrudeSpec(rect(10, 10, 30, 20), 30.0, "join", "one", 0.0, "Post sketch", "Post extrude")
ROUNDS = {
    "RoundTopEdge": (base(), FilletSpec((20.0, 0.0), 3.0, "Top round", LevelMm=20.0)),
    "BevelTopEdge": (base(), ChamferSpec((20.0, 0.0), 3.0, "Top bevel", LevelMm=20.0)),
    "BevelTopTwo": (base(), ChamferSpec((20.0, 0.0), 3.0, "Top bevel", 2.0, LevelMm=20.0)),
    "BevelTopAngle": (base(), ChamferSpec((20.0, 0.0), 3.0, "Top bevel", 0.0, 30.0, LevelMm=20.0)),
    "RoundTwoEdges": (base(), FilletSpec((20.0, 0.0), 3.0, "Top rounds", ((20.0, 30.0),), LevelMm=20.0)),
    "RoundBottomEdge": (base(), FilletSpec((40.0, 15.0), 2.0, "Bottom round", LevelMm=0.0)),
    "RoundDiscRim": (ROUND_DISC, FilletSpec((10.0, 0.0), 3.0, "Rim round", LevelMm=20.0)),
    "BevelDiscRim": (ROUND_DISC, ChamferSpec((10.0, 0.0), 2.0, "Rim bevel", LevelMm=20.0)),
    "RoundBossBase": (base(), hole(5, 30, "join", "Boss"), FilletSpec((25.0, 15.0), 2.0, "Boss round", LevelMm=20.0)),
    "RoundHoleRim": (base(), hole(5, 20, "cut", "Bore"), FilletSpec((25.0, 15.0), 2.0, "Bore round", LevelMm=20.0)),
    "RoundRimChain": (base(), CORNER_ROUNDS, FilletSpec((20.0, 0.0), 2.0, "Top chain", LevelMm=20.0)),
    "BevelRimChain": (base(), CORNER_ROUNDS, ChamferSpec((20.0, 0.0), 2.0, "Top bevel chain", LevelMm=20.0)),
    "RoundSlotRim": (SLOT_BAR, FilletSpec((20.0, 7.0), 2.0, "Slot round", LevelMm=20.0)),
    "BevelBottomTwo": (base(), ChamferSpec((40.0, 15.0), 3.0, "Bottom bevel", 2.0, LevelMm=0.0)),
    "BevelSideAngle": (base(), ChamferSpec((40.0, 15.0), 3.0, "Side bevel", 0.0, 30.0, LevelMm=20.0)),
    "BevelDiscTwo": (ROUND_DISC, ChamferSpec((10.0, 0.0), 3.0, "Rim bevel", 2.0, LevelMm=20.0)),
    "BevelBoreAngle": (base(), hole(5, 20, "cut", "Bore"), ChamferSpec((25.0, 15.0), 2.0, "Bore bevel", 0.0, 30.0, LevelMm=20.0)),
    "BevelTopLoop": (base(), ChamferSpec((20.0, 0.0), 2.0, "Top loop bevel", MoreCornersMm=((40.0, 15.0), (20.0, 30.0), (0.0, 15.0)), LevelMm=20.0)),
    "RoundTopLoop": (base(), FilletSpec((20.0, 0.0), 2.0, "Top loop round", ((40.0, 15.0), (20.0, 30.0), (0.0, 15.0)), LevelMm=20.0)),
    "RoundTopPair": (base(), FilletSpec((20.0, 0.0), 3.0, "Top pair round", ((40.0, 15.0),), LevelMm=20.0)),
    "RoundBottomLoop": (base(), FilletSpec((20.0, 0.0), 2.0, "Bottom loop round", ((40.0, 15.0), (20.0, 30.0), (0.0, 15.0)), LevelMm=0.0)),
    "BevelBossTwo": (base(), hole(5, 30, "join", "Boss"), ChamferSpec((25.0, 15.0), 2.0, "Boss bevel", 1.0, LevelMm=20.0)),
    "BevelDiscBottom": (ROUND_DISC, ChamferSpec((10.0, 0.0), 3.0, "Rim bevel", 0.0, 30.0, LevelMm=0.0)),
    "BevelRimTwo": (base(), CORNER_ROUNDS, ChamferSpec((20.0, 0.0), 2.0, "Top bevel chain", 1.0, LevelMm=20.0)),
    "BevelArcTwo": (base(), CORNER_ROUNDS, ChamferSpec((35.0 + 5.0 * 0.5**0.5, 5.0 - 5.0 * 0.5**0.5), 2.0, "Arc bevel chain", 1.0, LevelMm=20.0)),
    "BevelArcBottom": (base(), CORNER_ROUNDS, ChamferSpec((35.0 + 5.0 * 0.5**0.5, 5.0 - 5.0 * 0.5**0.5), 2.0, "Arc bevel chain", 1.0, LevelMm=0.0)),
    "RoundStepEdge": (STEP_BAR, FilletSpec((30.0, 15.0), 2.0, "Step round", LevelMm=20.0)),
    "BevelStepTwo": (STEP_BAR, ChamferSpec((30.0, 15.0), 2.0, "Step bevel", 1.0, LevelMm=20.0)),
    "RoundPostEdge": (base(), SQUARE_POST, FilletSpec((20.0, 10.0), 2.0, "Post round", LevelMm=20.0)),
    "BevelPostTwo": (base(), SQUARE_POST, ChamferSpec((20.0, 10.0), 2.0, "Post bevel", 1.0, LevelMm=20.0)),
}
PART.update(ROUNDS)
CASES.update(ROUNDS)
EDITS.update({
    "RoundTopEdge": [{"feature": "Top round", "role": "Radius", "expression": "4 mm"}],
    "BevelTopEdge": [{"feature": "Top bevel", "expression": "2 mm"}],
    "BevelTopTwo": [{"feature": "Top bevel", "role": "Distance 2", "expression": "1 mm"}],
    "BevelTopAngle": [{"feature": "Top bevel", "role": "Rotate Angle", "expression": "40 deg"}],
    "RoundTwoEdges": [{"feature": "Top rounds", "role": "Radius", "expression": "4 mm"}],
    "RoundBottomEdge": [{"feature": "Bottom round", "role": "Radius", "expression": "3 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "RoundDiscRim": [{"feature": "Rim round", "role": "Radius", "expression": "2 mm"}],
    "BevelDiscRim": [{"feature": "Rim bevel", "expression": "3 mm"}],
    "RoundBossBase": [{"feature": "Boss round", "role": "Radius", "expression": "3 mm"}],
    "RoundHoleRim": [{"feature": "Bore round", "role": "Radius", "expression": "1 mm"}],
    "RoundRimChain": [{"feature": "Top chain", "role": "Radius", "expression": "3 mm"}],
    "BevelRimChain": [{"feature": "Top bevel chain", "expression": "1 mm"}],
    "RoundSlotRim": [{"feature": "Slot round", "role": "Radius", "expression": "3 mm"}],
    "BevelBottomTwo": [{"feature": "Bottom bevel", "role": "Distance 2", "expression": "1 mm"}],
    "BevelSideAngle": [{"feature": "Side bevel", "role": "Rotate Angle", "expression": "40 deg"}],
    "BevelDiscTwo": [{"feature": "Rim bevel", "role": "Distance 2", "expression": "1 mm"}],
    "BevelBoreAngle": [{"feature": "Bore bevel", "role": "Rotate Angle", "expression": "40 deg"}],
    "BevelTopLoop": [{"feature": "Top loop bevel", "expression": "3 mm"}],
    "RoundTopLoop": [{"feature": "Top loop round", "role": "Radius", "expression": "3 mm"}],
    "RoundTopPair": [{"feature": "Top pair round", "role": "Radius", "expression": "2 mm"}],
    "RoundBottomLoop": [{"feature": "Bottom loop round", "role": "Radius", "expression": "3 mm"}],
    "BevelBossTwo": [{"feature": "Boss bevel", "role": "Distance 2", "expression": "1.5 mm"}],
    "BevelDiscBottom": [{"feature": "Rim bevel", "role": "Rotate Angle", "expression": "40 deg"}],
    "BevelRimTwo": [{"feature": "Top bevel chain", "role": "Distance 2", "expression": "1.5 mm"}],
    "BevelArcTwo": [{"feature": "Arc bevel chain", "role": "Distance 2", "expression": "1.5 mm"}],
    "BevelArcBottom": [{"feature": "Arc bevel chain", "role": "Distance 2", "expression": "1.5 mm"}],
    "RoundStepEdge": [{"feature": "Step round", "role": "Radius", "expression": "3 mm"}],
    "BevelStepTwo": [{"feature": "Step bevel", "role": "Distance 2", "expression": "1.5 mm"}],
    "RoundPostEdge": [{"feature": "Post round", "role": "Radius", "expression": "3 mm"}],
    "BevelPostTwo": [{"feature": "Post bevel", "role": "Distance 2", "expression": "1.5 mm"}],
})

def mm(value):
    return f"{value:g} mm"


def curve_step(curve):
    if isinstance(curve, LineCurve):
        return {"kind": "line", "start_cm": [v / 10.0 for v in curve.StartMm], "end_cm": [v / 10.0 for v in curve.FinishMm]}
    if isinstance(curve, CircleCurve):
        return {"kind": "circle", "center_cm": [v / 10.0 for v in curve.CenterMm], "radius_cm": curve.RadiusMm / 10.0}
    start = math.radians(curve.StartDegrees)
    return {
        "kind": "arc",
        "center_cm": [v / 10.0 for v in curve.CenterMm],
        "start_cm": [(curve.CenterMm[0] + curve.RadiusMm * math.cos(start)) / 10.0, (curve.CenterMm[1] + curve.RadiusMm * math.sin(start)) / 10.0],
        "sweep_rad": math.radians(curve.SweepDegrees),
    }


def step(feature):
    if isinstance(feature, SweepSpec):
        return {
            "kind": "sweep",
            "profile_cm": [feature.LeftMm / 10.0, feature.RightMm / 10.0, feature.LowerMm / 10.0, feature.UpperMm / 10.0],
            "path": [curve_step(curve) for curve in feature.Path],
            "profile": feature.ProfileName,
            "path_name": feature.PathName,
            "name": feature.FeatureName,
        }
    if isinstance(feature, LoftSpec):
        return {
            "kind": "loft",
            "lower_profile": [curve_step(curve) for curve in feature.LowerProfile],
            "upper_profile": [curve_step(curve) for curve in feature.UpperProfile],
            "height": mm(feature.HeightMm),
            "lower": feature.LowerName,
            "plane": feature.PlaneName,
            "upper": feature.UpperName,
            "name": feature.FeatureName,
        }
    if isinstance(feature, CombineSpec):
        return {"kind": "combine", "target": feature.TargetBody, "tools": list(feature.ToolBodies), "operation": feature.Operation, "keep": feature.KeepTools, "name": feature.FeatureName}
    if isinstance(feature, PasteSpec):
        return {"kind": "paste", "source_body": feature.SourceBody, "name": feature.FeatureName}
    if isinstance(feature, SplitSpec):
        return {"kind": "split", "plane": feature.PlaneIndex, "target": feature.TargetBody, "name": feature.FeatureName}
    if isinstance(feature, BodyGridSpec):
        return {"kind": "body_pattern", "source_body": feature.SourceBody, "count_u": feature.CountU, "spacing_u": mm(feature.SpacingUMm), "count_v": feature.CountV, "spacing_v": mm(feature.SpacingVMm), "name": feature.FeatureName}
    if isinstance(feature, BodyRingSpec):
        return {"kind": "body_ring", "source_body": feature.SourceBody, "count": feature.Count, "angle": f"{feature.TotalDegrees:g} deg", "name": feature.FeatureName}
    if isinstance(feature, ExtrudeSpec):
        return {
            "kind": "extrude",
            "profile": [curve_step(curve) for curve in feature.Profile],
            "amount": mm(feature.DistanceMm),
            "against": mm(feature.AgainstMm),
            "operation": feature.Operation,
            "extent": feature.Extent,
            "sketch": feature.SketchName,
            "name": feature.FeatureName,
        }
    if isinstance(feature, DraftSpec):
        return {"kind": "draft", "angle": f"{feature.AngleDegrees:g} deg", "name": feature.FeatureName}
    if isinstance(feature, OffsetSpec):
        result = {"kind": "offset", "amount": mm(feature.DistanceMm), "name": feature.FeatureName}
        if feature.SideMm is not None:
            result["side_cm"] = [feature.SideMm[0] / 10.0, feature.SideMm[1] / 10.0]
        return result
    if isinstance(feature, MoveSpec):
        return {"kind": "move", "offset_cm": [v / 10.0 for v in feature.OffsetMm], "turn_degrees": feature.TurnDegrees, "name": feature.FeatureName}
    if isinstance(feature, RevolveSpec):
        return {
            "kind": "revolve",
            "inner_cm": feature.InnerMm / 10.0,
            "outer_cm": feature.OuterMm / 10.0,
            "lower_cm": feature.LowerMm / 10.0,
            "upper_cm": feature.UpperMm / 10.0,
            "angle": f"{feature.AngleDegrees:g} deg",
            "operation": feature.Operation,
            "sketch": feature.SketchName,
            "name": feature.FeatureName,
        }
    if isinstance(feature, HoleSpec):
        result = {"kind": "hole", "center_cm": [v / 10.0 for v in feature.CenterMm], "diameter": mm(feature.DiameterMm), "name": feature.FeatureName}
        if feature.DepthMm:
            result["depth"] = mm(feature.DepthMm)
        if feature.BoreDiameterMm:
            result.update(bore_diameter=mm(feature.BoreDiameterMm), bore_depth=mm(feature.BoreDepthMm))
        if feature.SinkDiameterMm:
            result.update(sink_diameter=mm(feature.SinkDiameterMm), sink_angle=f"{feature.SinkAngleDegrees:g} deg")
        return result
    if isinstance(feature, ShellSpec):
        result = {"kind": "shell", "amount": mm(feature.ThicknessMm), "name": feature.FeatureName}
        if feature.SidesMm:
            result["sides_cm"] = [[x / 10.0, y / 10.0] for x, y in feature.SidesMm]
        return result
    if isinstance(feature, PatternSpec):
        return {"kind": "pattern", "source": feature.SourceIndex, "count_u": feature.CountU, "spacing_u": mm(feature.SpacingUMm), "count_v": feature.CountV, "spacing_v": mm(feature.SpacingVMm), "name": feature.FeatureName}
    if isinstance(feature, CircularSpec):
        return {"kind": "circular", "source": feature.SourceIndex, "count": feature.Count, "angle": f"{feature.TotalDegrees:g} deg", "name": feature.FeatureName}
    if isinstance(feature, PlaneSpec):
        return {"kind": "plane", "base": feature.BasePlane, "offset": mm(feature.OffsetMm), "name": feature.FeatureName}
    if isinstance(feature, MirrorSpec):
        return {"kind": "mirror", "source": feature.SourceIndex, "plane": feature.PlaneIndex, "name": feature.FeatureName}
    if isinstance(feature, (AxisSpec, PointSpec)):
        kind = "axis" if isinstance(feature, AxisSpec) else "point"
        return {"kind": kind, "corner_cm": [feature.CornerMm[0] / 10.0, feature.CornerMm[1] / 10.0], "name": feature.FeatureName}
    amount = feature.RadiusMm if isinstance(feature, FilletSpec) else feature.DistanceMm
    result = {
        "kind": "fillet" if isinstance(feature, FilletSpec) else "chamfer",
        "corner_cm": [feature.CornerMm[0] / 10.0, feature.CornerMm[1] / 10.0],
        "amount": mm(amount),
        "name": feature.FeatureName,
    }
    if feature.MoreCornersMm:
        result["corners_cm"] = [[x / 10.0, y / 10.0] for x, y in (feature.CornerMm, *feature.MoreCornersMm)]
    if isinstance(feature, ChamferSpec) and feature.SecondMm:
        result["second"] = mm(feature.SecondMm)
    if isinstance(feature, ChamferSpec) and feature.AngleDegrees:
        result["angle"] = f"{feature.AngleDegrees:g} deg"
    if feature.LevelMm is not None:
        result["level_cm"] = feature.LevelMm / 10.0
    return result


def expectation(solid):
    shape = BuildShape(solid)
    edges = {use.Edge for face in shape.Faces for loop in face.Loops for use in loop}
    mass = SolidMass(solid)
    return {"volume_cm3": mass["volume"], "area_cm2": mass["area"], "faces": len(shape.Faces), "edges": len(edges)}


def spec(name, features):
    if name in PART:
        return DocumentSpec(Title="Kit " + name, ParamName="height", LengthMm=20.0, ProfileKind="part", BodyName="Body1", Features=features)
    return DocumentSpec(
        Title="Kit " + name,
        ParamName="height",
        LengthMm=20.0,
        ProfileKind="cuboid",
        SketchName="Base Sketch",
        ExtrusionName="Base Extrude",
        BodyName="Body1",
        WidthMm=40.0,
        DepthMm=30.0,
        Features=features,
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    unknown = only - set(CASES)
    if unknown:
        raise SystemExit("Unknown cases: " + ", ".join(sorted(unknown)))
    path = OUTPUT / "Manifest.json"
    manifest = json.loads(path.read_text()) if only and path.exists() else {}
    for name, features in CASES.items():
        if only and name not in only:
            continue
        value = spec(name, features)
        payload = EmitDocument(value)
        start, stages = SolvePart(value)
        target = OUTPUT / (name + ".f3d")
        target.write_bytes(payload)
        solids = ([] if start is None else [start]) + [stage.After for stage in stages]
        bodies = [expectation(solid) for solid in stages[-1].Bodies if solid.Ordinal in stages[-1].Shown] if stages else []
        manifest[name] = {
            "file": target.name,
            "base": "part" if name in PART else "cuboid",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "features": [repr(feature) for feature in features],
            "steps": [step(feature) for feature in features],
            "edits": EDITS[name],
            "kit_states": [expectation(solid) for solid in solids],
            "kit_bodies": bodies,
        }
        print(name, len(payload), manifest[name]["sha256"][:16], manifest[name]["kit_states"][-1])
    path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
