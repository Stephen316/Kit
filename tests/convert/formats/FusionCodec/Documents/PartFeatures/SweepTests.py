from math import inf as KInfinity, nan as KNotNumber, pi as KCirclePi
from typing import cast as CastValue

from pytest import approx as ApproxValue, mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import (
    MeasurePart,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import (
    PlaneSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    KPathCurve,
    SweepSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.formats.Fusion.DocumentCodec.PartFeatures.Sweep.SweepTags import (
    FaceIds,
    SweepTags,
)
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.PartFeatures.BodyTests import (
    RectCurves,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.BulletinRefs import (
    IsIdentityRef,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    KBlock,
    FamilySpec,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.NativeControl import (
    NativeBodies,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)

KLine = LineCurve((0.0, 0.0), (0.0, 20.0))
KBend: tuple[KPathCurve, ...] = (KLine, ArcCurve((-30.0, 20.0), 30.0, 0.0, 90.0))
KHook = (*KBend, LineCurve((-30.0, 50.0), (-50.0, 50.0)))
KCurve: tuple[KPathCurve, ...] = (
    LineCurve((0.0, 0.0), (0.0, 10.0)),
    ArcCurve((20.0, 10.0), 20.0, 180.0, -90.0),
    ArcCurve((20.0, 50.0), 20.0, -90.0, 90.0),
)
KSweep = SweepSpec(KBend, -5.0, 5.0, 0.0, 10.0, FeatureName="Bend sweep")
KRail = SweepSpec(
    KBend, -15.0, -5.0, 0.0, 10.0, "Rail profile", "Rail path", "Rail sweep"
)
KSweepCases: dict[str, tuple[KPartFeature, ...]] = {
    "SweepBend": (KSweep,),
    "SweepHook": (SweepSpec(KHook, -5.0, 5.0, 0.0, 10.0, FeatureName="Bend sweep"),),
    "SweepSCurve": (
        SweepSpec(KCurve, -3.0, 5.0, 2.0, 8.0, "Bar profile", "Bar path", "Bar sweep"),
    ),
    "SweepSecondBody": (KBlock, KRail),
}


@MarkTests.parametrize("NameValue", ("SweepBend", "SweepHook"))
def TestSweepSolid(NameValue: str) -> None:
    _, Stages = SolvePart(FamilySpec(KSweepCases[NameValue]))
    (Observed,) = NativeBodies(NameValue)
    Measured = MeasurePart(Stages[-1].After)
    assert (Measured.FaceCount, Measured.EdgeCount) == (
        Observed["faces"],
        Observed["edges"],
    )
    assert Measured.VolumeCm == ApproxValue(Observed["volume_cm3"], rel=1e-7)
    assert Measured.AreaCm == ApproxValue(Observed["area_cm2"], rel=1e-7)


@MarkTests.parametrize(
    ("NameValue", "LengthMm", "AreaCm", "Counts"),
    (
        ("SweepBend", 20.0 + 15.0 * KCirclePi, 1.0, (8, 18)),
        ("SweepHook", 40.0 + 15.0 * KCirclePi, 1.0, (10, 24)),
        ("SweepSCurve", 10.0 + 20.0 * KCirclePi, 0.48, (10, 24)),
        ("SweepSecondBody", 20.0 + 10.0 * KCirclePi, 1.0, (8, 18)),
    ),
)
def TestSweepVolume(
    NameValue: str, LengthMm: float, AreaCm: float, Counts: tuple[int, int]
) -> None:
    _, Stages = SolvePart(FamilySpec(KSweepCases[NameValue]))
    Final = Stages[-1]
    assert Final.Shown == tuple(range(1, len(Final.Bodies) + 1))
    Measured = MeasurePart(Final.Bodies[-1])
    assert (Measured.FaceCount, Measured.EdgeCount) == Counts
    assert Measured.VolumeCm == ApproxValue(AreaCm * LengthMm / 10.0, rel=1e-9)


def TestSweepStages() -> None:
    _, Stages = SolvePart(FamilySpec(KSweepCases["SweepBend"]))
    (Stage,) = Stages
    assert (Stage.Operations, Stage.StateId) == ((300, 301, 302), 4)
    assert Stage.Sketch is not None and Stage.Upper is not None
    assert (Stage.Sketch.Ordinal, Stage.Sketch.NextTag) == (1, 109)
    assert (Stage.Upper.Ordinal, Stage.Upper.NextTag) == (2, 116)
    assert [EdgeValue.CurveTag for EdgeValue in Stage.Upper.Edges] == [114, 115]
    _, Stages = SolvePart(FamilySpec(KSweepCases["SweepSecondBody"]))
    assert [Stage.Operations for Stage in Stages] == [
        (300, 301, 302),
        (303, 304, 305),
    ]
    assert [Stage.StateId for Stage in Stages] == [4, 5]


@MarkTests.parametrize("NameValue", tuple(KSweepCases))
def TestSweepParts(NameValue: str) -> None:
    Features = KSweepCases[NameValue]
    SweepValue = CastValue(SweepSpec, Features[-1])
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    assert ReadDocument(EmitParsed(Model)) == Model
    Count = len(SweepValue.Path)
    ArcCount = sum(isinstance(Curve, ArcCurve) for Curve in SweepValue.Path)
    Expected = {
        "DcSweepFeature": 1,
        "DcSweepToolBody": 1,
        "SweepFaceProgenitor": 4 * Count,
        "SketchCurveEntityRecipe": 3 * Count,
        "SketchEntityRecipe": 4 * Count,
        "ETCachedCircleArc": ArcCount,
        "ETCachedLineSeg3d": Count - ArcCount,
        "DcSketch": len(Features) + 1,
        "MSketch": len(Features) + 1,
        "Body": len(Features),
    }
    for ClassName, Total in Expected.items():
        assert len(PartRecords(Model, ClassName)) == Total
    (Feature,) = PartRecords(Model, "DcSweepFeature")
    assert (Feature["booleanOperation"], Feature["featureUserName"]) == (
        4,
        SweepValue.FeatureName,
    )
    Names = [Fields["userName"] for Fields in PartRecords(Model, "Sketch")]
    assert Names[-2:] == [SweepValue.ProfileName, SweepValue.PathName]
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert IsIdentityRef(History)


def TestSweepTags() -> None:
    TagMap = SweepTags(2)
    assert list(TagMap) == [
        (2, 1),
        (2, 0),
        (1, 0),
        (0, 1),
        (0, 0),
        (3, 0),
        (1, 1),
        (3, 1),
    ]
    assert list(TagMap.values()) == list(range(5, 13))
    assert FaceIds(TagMap) == (b"10", b"11", b"12", b"5", b"5", b"7", b"8", b"8")


@MarkTests.parametrize(
    ("NameValue", "TableTag", "Labels"),
    (
        ("SweepBend", 14, (49, 48, 49, 49, 49, 50, 53, 53, 55, 56, 56)),
        (
            "SweepHook",
            19,
            (49, 48, 49, 48, 49, 48, 49, 51, 49, 52, 49, 53)
            + (49, 54, 49, 55, 54, 54, 54, 57),
        ),
    ),
)
def TestSweepTable(NameValue: str, TableTag: int, Labels: tuple[int, ...]) -> None:
    Model = ReadDocument(EmitDocument(FamilySpec(KSweepCases[NameValue])))
    Tables = [
        Fields
        for Fields in PartRecords(Model, "ProgenitorTable")
        if Fields["tagId"] == TableTag
    ]
    assert len(Tables) == 1
    (SeedFields,) = PartRecords(Model, "BodyProgenitor")
    MapText = repr(SeedFields["featureTagOccMap"])
    assert "Items=" + repr(Labels) in MapText
    assert "operationId', Value=302" in MapText


def PathCase(*Curves: KPathCurve) -> tuple[KPartFeature, ...]:
    return (SweepSpec(Curves, -5.0, 5.0, 0.0, 10.0),)


KValueRejects: tuple[tuple[KPartFeature, ...], ...] = (
    PathCase(),
    (SweepSpec(CastValue(tuple[KPathCurve, ...], list(KBend)), -5.0, 5.0, 0.0, 10.0),),
    PathCase(CastValue(KPathCurve, CircleCurve((0.0, 0.0), 5.0))),
    (SweepSpec(KBend, 5.0, 5.0, 0.0, 10.0),),
    (SweepSpec(KBend, -5.0, 5.0, 10.0, 10.0),),
    (SweepSpec(KBend, KNotNumber, 5.0, 0.0, 10.0),),
    (SweepSpec(KBend, -5.0, 5.0, 0.0, KInfinity),),
    (SweepSpec(KBend, True, 5.0, 0.0, 10.0),),
    (SweepSpec(KBend, -5.0, 5.0, 0.0, 10.0, PathName=""),),
    (SweepSpec(KBend, -5.0, 5.0, 0.0, 10.0, FeatureName="a\x00b"),),
)
KTwinArc = (
    ArcCurve((-30.0, 20.0), 30.0, 0.0, 45.0),
    ArcCurve((-30.0, 20.0), 30.0, 45.0, 45.0),
)
KLoopPath = (
    KLine,
    ArcCurve((-10.0, 20.0), 10.0, 0.0, 270.0),
    LineCurve((-10.0, 10.0), (10.0, 10.0)),
)
KPathRejects: tuple[tuple[KPartFeature, ...], ...] = (
    PathCase(LineCurve((5.0, 0.0), (5.0, 20.0))),
    PathCase(LineCurve((0.0, 0.0), (20.0, 0.0))),
    PathCase(LineCurve((0.0, 0.0), (0.0, -20.0))),
    PathCase(KLine, LineCurve((0.0, 25.0), (0.0, 40.0))),
    PathCase(KLine, LineCurve((0.0, 20.0), (20.0, 20.0))),
    PathCase(KLine, LineCurve((0.0, 20.0), (0.0, 40.0))),
    PathCase(KLine, *KTwinArc),
    PathCase(KLine, ArcCurve((-3.0, 20.0), 3.0, 0.0, 90.0)),
    PathCase(KLine, ArcCurve((3.0, 20.0), 3.0, 90.0, 90.0)),
    (SweepSpec(KLoopPath, -2.0, 2.0, 0.0, 10.0),),
    PathCase(LineCurve((0.0, 0.0), (0.0, 0.0))),
)
KAfterRejects: tuple[tuple[KPartFeature, ...], ...] = (
    (KSweep, FilletSpec((5.0, 0.0), 1.0)),
    (KSweep, MoveSpec((5.0, 0.0, 0.0), "Move")),
    (KBlock, KRail, CombineSpec(1, (2,))),
    (KBlock, KRail, CombineSpec(2, (1,))),
    (KBlock, KRail, PlaneSpec(5.0, "xy", "Split plane"), SplitSpec(2, 2)),
    (KSweep, BodyGridSpec(1, 2, 80.0)),
    (KSweep, ExtrudeSpec(RectCurves((0.0, 0.0), (4.0, 4.0)), 5.0, "join")),
)


@MarkTests.parametrize("Features", (*KValueRejects, *KPathRejects, *KAfterRejects))
def TestSweepReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(FamilySpec(Features))


def TestSweepExtra() -> None:
    Extra = ExtrudeSpec(RectCurves((20.0, 20.0), (30.0, 30.0)), 5.0, "new")
    _, Stages = SolvePart(FamilySpec((KSweep, Extra)))
    assert Stages[-1].Shown == (1, 2)
    assert [Stage.Operations for Stage in Stages] == [
        (300, 301, 302),
        (303, 304, 305),
    ]


def TestSweepCuboid() -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(
            DocumentSpec("Cuboid", "height", 20.0, "cuboid", Features=(KSweep,))
        )
