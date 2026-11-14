from collections import Counter
from math import nan as KNotNumber, pi as KCirclePi

from pytest import approx as ApproxValue, mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import (
    MeasurePart,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EdgeCurve import EdgeEnds
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
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
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.PartFeatures.BodyTests import (
    RectCurves,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.BulletinRefs import (
    IsIdentityRef,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    KBlock,
    KFamilyNames,
    FamilySpec,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.NativeControl import (
    NativeControl,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)

KDisc = ExtrudeSpec(
    (CircleCurve((0.0, 0.0), 10.0),),
    20.0,
    "new",
    "one",
    0.0,
    "Disc sketch",
    "Disc extrude",
)
KCorners = FilletSpec(
    (40.0, 30.0), 5.0, "Corner rounds", ((0.0, 0.0), (40.0, 0.0), (0.0, 30.0))
)
KTopRound = FilletSpec((20.0, 0.0), 3.0, "Top round", LevelMm=20.0)
KRoundCases: dict[str, tuple[KPartFeature, ...]] = {
    "FilletTop": (KBlock, KTopRound),
    "ChamferTop": (KBlock, ChamferSpec((20.0, 0.0), 3.0, "Top bevel", LevelMm=20.0)),
    "FilletChain": (
        KBlock,
        KCorners,
        FilletSpec((20.0, 0.0), 2.0, "Top chain", LevelMm=20.0),
    ),
    "FilletRim": (KDisc, FilletSpec((10.0, 0.0), 3.0, "Rim round", LevelMm=20.0)),
}
KRoundTori = {"FilletTop": 0, "ChamferTop": 0, "FilletChain": 4, "FilletRim": 1}


@MarkTests.parametrize("NameValue", tuple(KRoundCases))
def TestRoundNative(NameValue: str) -> None:
    _, Stages = SolvePart(FamilySpec(KRoundCases[NameValue]))
    Measured = MeasurePart(Stages[-1].After)
    Native = NativeControl(NameValue)
    assert (Measured.FaceCount, Measured.EdgeCount) == (
        Native["faces"],
        Native["edges"],
    )
    assert Measured.VolumeCm == ApproxValue(Native["volume_cm3"], rel=1e-9)
    assert Measured.AreaCm == ApproxValue(Native["area_cm2"], rel=1e-9)


@MarkTests.parametrize("NameValue", tuple(KRoundCases))
def TestRoundFile(NameValue: str) -> None:
    Features = KRoundCases[NameValue]
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    assert ReadDocument(EmitParsed(Model)) == Model
    Expected = Counter(KFamilyNames[type(Feature)] for Feature in Features)
    for ClassName, Count in Expected.items():
        assert len(PartRecords(Model, ClassName)) == Count
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert IsIdentityRef(History)
    TorusList = [Entity for Entity in History.Entities if isinstance(Entity, TorusNode)]
    assert len(TorusList) == KRoundTori[NameValue]


def TestRoundLegs() -> None:
    EvenVolume = MeasurePart(
        SolvePart(FamilySpec(KRoundCases["ChamferTop"]))[1][-1].After
    ).VolumeCm
    Uneven = ChamferSpec((20.0, 0.0), 3.0, "Top bevel", 2.0, LevelMm=20.0)
    Measured = MeasurePart(SolvePart(FamilySpec((KBlock, Uneven)))[1][-1].After)
    assert EvenVolume == ApproxValue(24.0 - 0.3 * 0.3 / 2.0 * 4.0, rel=1e-12)
    assert Measured.VolumeCm == ApproxValue(24.0 - 0.3 * 0.2 / 2.0 * 4.0, rel=1e-12)


def ShapePoints(Features: tuple[KPartFeature, ...]) -> set[tuple[float, ...]]:
    Shape = BuildShape(SolvePart(FamilySpec(Features))[1][-1].After)
    return {
        tuple(round(Value, 9) for Value in Point)
        for FaceValue in Shape.Faces
        for RingValue in FaceValue.Loops
        for UseValue in RingValue
        for Point in EdgeEnds(UseValue.Edge)
    }


KArcPoint = (35.0 + 5.0 * 0.5**0.5, 5.0 - 5.0 * 0.5**0.5)


@MarkTests.parametrize(
    ("Features", "Corners"),
    (
        (
            (KBlock, ChamferSpec((20.0, 0.0), 3.0, "Top", 2.0, LevelMm=20.0)),
            ((0.0, 0.3, 2.0), (0.0, 0.0, 1.8)),
        ),
        (
            (KBlock, ChamferSpec((40.0, 15.0), 3.0, "Bottom", 2.0, LevelMm=0.0)),
            ((3.8, 0.0, 0.0), (4.0, 0.0, 0.3)),
        ),
        (
            (KBlock, KCorners, ChamferSpec((20.0, 0.0), 2.0, "Rim", 1.0, LevelMm=20.0)),
            ((0.5, 0.2, 2.0), (0.5, 0.0, 1.9)),
        ),
        (
            (KBlock, KCorners, ChamferSpec(KArcPoint, 2.0, "Arc", 1.0, LevelMm=20.0)),
            ((0.5, 0.1, 2.0), (0.5, 0.0, 1.8)),
        ),
    ),
)
def TestRoundSides(
    Features: tuple[KPartFeature, ...], Corners: tuple[tuple[float, ...], ...]
) -> None:
    assert set(Corners) <= ShapePoints(Features)


KLoopPoints = ((40.0, 15.0), (20.0, 30.0), (0.0, 15.0))


def LoopVolume(Section: float, Moment: float) -> float:
    return 24.0 - (14.0 * Section - 8.0 * Moment)


@MarkTests.parametrize(
    ("Feature", "Volume"),
    (
        (
            ChamferSpec((20.0, 0.0), 2.0, MoreCornersMm=KLoopPoints, LevelMm=20.0),
            LoopVolume(0.02, 0.2**3 / 6.0),
        ),
        (
            FilletSpec((20.0, 0.0), 2.0, "Loop", KLoopPoints, LevelMm=20.0),
            LoopVolume(
                0.04 * (1.0 - KCirclePi / 4.0), 0.008 * (5.0 / 6.0 - KCirclePi / 4.0)
            ),
        ),
        (
            FilletSpec((20.0, 0.0), 2.0, "Loop", KLoopPoints, LevelMm=0.0),
            LoopVolume(
                0.04 * (1.0 - KCirclePi / 4.0), 0.008 * (5.0 / 6.0 - KCirclePi / 4.0)
            ),
        ),
    ),
)
def TestRoundLoops(Feature: KPartFeature, Volume: float) -> None:
    _, Stages = SolvePart(FamilySpec((KBlock, Feature)))
    Measured = MeasurePart(Stages[-1].After)
    assert (Measured.FaceCount, Measured.EdgeCount) == (10, 20)
    assert Measured.VolumeCm == ApproxValue(Volume, rel=1e-12)
    Model = ReadDocument(EmitDocument(FamilySpec((KBlock, Feature))))
    assert len(PartRecords(Model, KFamilyNames[type(Feature)])) == 1


KTrapezoid = ExtrudeSpec(
    (
        LineCurve((0.0, 0.0), (40.0, 0.0)),
        LineCurve((40.0, 0.0), (30.0, 30.0)),
        LineCurve((30.0, 30.0), (10.0, 30.0)),
        LineCurve((10.0, 30.0), (0.0, 0.0)),
    ),
    20.0,
    "new",
)
KRoundRejects: tuple[tuple[KPartFeature, ...], ...] = (
    (KBlock, FilletSpec((20.0, 15.0), 3.0, LevelMm=20.0)),
    (KBlock, FilletSpec((20.0, 0.0), 3.0, LevelMm=10.0)),
    (KBlock, FilletSpec((20.0, 0.0), 3.0, LevelMm=KNotNumber)),
    (KTrapezoid, FilletSpec((20.0, 0.0), 3.0, LevelMm=20.0)),
    (
        KBlock,
        KTopRound,
        ExtrudeSpec(RectCurves((5.0, 5.0), (10.0, 10.0)), 5.0, "join"),
    ),
)


@MarkTests.parametrize("Features", KRoundRejects)
def TestRoundReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(FamilySpec(Features))
