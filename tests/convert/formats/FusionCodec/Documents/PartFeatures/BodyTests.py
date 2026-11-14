from collections import Counter
from typing import Literal

from pytest import approx as ApproxValue, mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import (
    MeasurePart,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyRingSpec import (
    BodyRingSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import (
    PlaneSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.SplitSpec import SplitSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
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


def RectCurves(
    Lower: tuple[float, float], Upper: tuple[float, float]
) -> tuple[LineCurve, ...]:
    Corners = (Lower, (Upper[0], Lower[1]), Upper, (Lower[0], Upper[1]))
    return tuple(
        LineCurve(Corners[Index], Corners[(Index + 1) % 4]) for Index in range(4)
    )


KPost = ExtrudeSpec(
    (CircleCurve((40.0, 30.0), 10.0),),
    20.0,
    "new",
    "one",
    0.0,
    "Post sketch",
    "Post extrude",
)
KCube = ExtrudeSpec(
    RectCurves((0.0, 0.0), (10.0, 10.0)),
    10.0,
    "new",
    "one",
    0.0,
    "Cube sketch",
    "Cube extrude",
)
KRingCube = ExtrudeSpec(
    RectCurves((20.0, -5.0), (30.0, 5.0)),
    10.0,
    "new",
    "one",
    0.0,
    "Cube sketch",
    "Cube extrude",
)
KSecond = ExtrudeSpec(
    (CircleCurve((60.0, 15.0), 5.0),),
    20.0,
    "new",
    "one",
    0.0,
    "Post sketch",
    "Post extrude",
)
KRingBody = RevolveSpec(
    60.0, 80.0, 0.0, 10.0, 360.0, "new", "Ring sketch", "Ring revolve"
)


def CombineCase(
    Operation: Literal["join", "cut", "intersect"], IsKept: bool
) -> tuple[KPartFeature, ...]:
    return (KBlock, KPost, CombineSpec(1, (2,), Operation, IsKept, "Body combine"))


def SplitCase(
    OffsetMm: float, BasePlane: Literal["xy", "yz", "xz"]
) -> tuple[KPartFeature, ...]:
    return (
        KBlock,
        PlaneSpec(OffsetMm, BasePlane, "Split plane"),
        SplitSpec(1, 1, "Body split"),
    )


KBodyCases: dict[str, tuple[tuple[KPartFeature, ...], str]] = {
    "ExtrudeSecondBody": ((KBlock, KSecond), "ExtrudeSecondBody"),
    "RevolveBody": ((KBlock, KRingBody), "RevolveBody"),
    "CombineJoin": (CombineCase("join", False), "Combine"),
    "CombineCut": (CombineCase("cut", False), "CombineCut"),
    "CombineIntersect": (CombineCase("intersect", False), "CombineIntersect"),
    "CombineKeep": (CombineCase("join", True), "CombineKeep"),
    "SplitYZ": (SplitCase(20.0, "yz"), "SplitBody"),
    "SplitXZ": (SplitCase(10.0, "xz"), "SplitXZ"),
    "SplitXY": (SplitCase(8.0, "xy"), "SplitXY"),
    "BodyRectPattern": (
        (KCube, BodyGridSpec(1, 3, 15.0, 2, 20.0, "Cube grid")),
        "BodyRectPattern",
    ),
    "BodyCircPattern": (
        (KRingCube, BodyRingSpec(1, 4, 360.0, "Cube ring")),
        "BodyCircPattern",
    ),
}
KBodyNames: dict[type[object], str] = {
    ExtrudeSpec: "DcExtrudeFeature",
    RevolveSpec: "DcRevolveFeature",
    PlaneSpec: "DcWorkPlane",
    CombineSpec: "DcCombineFeature",
    SplitSpec: "DcSplitBodyFeature",
    BodyGridSpec: "DcRectangularPattern",
    BodyRingSpec: "DcCircularPattern",
}


@MarkTests.parametrize("NameValue", tuple(KBodyCases))
def TestBodySolid(NameValue: str) -> None:
    Features, Control = KBodyCases[NameValue]
    _, Stages = SolvePart(FamilySpec(Features))
    Final = Stages[-1]
    Shown = [Solid for Solid in Final.Bodies if Solid.Ordinal in Final.Shown]
    Native = NativeBodies(Control)
    assert len(Shown) == len(Native)
    for Solid, Observed in zip(Shown, Native):
        Measured = MeasurePart(Solid)
        assert (Measured.FaceCount, Measured.EdgeCount) == (
            Observed["faces"],
            Observed["edges"],
        )
        assert Measured.VolumeCm == ApproxValue(Observed["volume_cm3"], rel=1e-7)
        assert Measured.AreaCm == ApproxValue(Observed["area_cm2"], rel=1e-7)


@MarkTests.parametrize("NameValue", tuple(KBodyCases))
def TestBodyArchive(NameValue: str) -> None:
    Features = KBodyCases[NameValue][0]
    _, Stages = SolvePart(FamilySpec(Features))
    Final = Stages[-1]
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    assert ReadDocument(EmitParsed(Model)) == Model
    Expected = Counter(KBodyNames[type(Feature)] for Feature in Features)
    for ClassName, Count in Expected.items():
        assert len(PartRecords(Model, ClassName)) == Count
    Occurrences = sum(
        isinstance(Feature, (CombineSpec, SplitSpec)) for Feature in Features
    )
    assert len(PartRecords(Model, "OccurrenceDataRef")) == Occurrences
    Bodies = PartRecords(Model, "Body")
    assert [Fields["creationIndex"] for Fields in Bodies] == [
        Solid.Ordinal for Solid in Final.Bodies
    ]
    assert [Fields["isVisible"] for Fields in Bodies] == [
        Solid.Ordinal in Final.Shown for Solid in Final.Bodies
    ]
    assert [Fields["isEliminated"] for Fields in PartRecords(Model, "DcBody")] == [
        Solid.Ordinal not in Final.Shown for Solid in Final.Bodies
    ]
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert IsIdentityRef(History)


KShownCases: tuple[tuple[str, tuple[int, ...], tuple[int, ...]], ...] = (
    ("ExtrudeSecondBody", (1, 2), (1, 2)),
    ("CombineJoin", (1,), (1, 2)),
    ("CombineIntersect", (1,), (1, 2)),
    ("CombineKeep", (1, 2), (1, 2)),
    ("SplitXY", (1, 2), (1, 2)),
    ("BodyRectPattern", (1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6)),
    ("BodyCircPattern", (1, 2, 3, 4), (1, 2, 3, 4)),
)


@MarkTests.parametrize(("NameValue", "Shown", "Ordinals"), KShownCases)
def TestBodyShown(
    NameValue: str, Shown: tuple[int, ...], Ordinals: tuple[int, ...]
) -> None:
    _, Stages = SolvePart(FamilySpec(KBodyCases[NameValue][0]))
    assert Stages[-1].Shown == Shown
    assert tuple(Solid.Ordinal for Solid in Stages[-1].Bodies) == Ordinals


@MarkTests.parametrize(
    ("NameValue", "Operation", "IsKept"),
    (
        ("CombineJoin", 0, False),
        ("CombineCut", 1, False),
        ("CombineIntersect", 2, False),
        ("CombineKeep", 0, True),
    ),
)
def TestBodyCombine(NameValue: str, Operation: int, IsKept: bool) -> None:
    Model = ReadDocument(EmitDocument(FamilySpec(KBodyCases[NameValue][0])))
    Fields = PartRecords(Model, "DcCombineFeature")[0]
    assert (Fields["booleanOperation"], Fields["isKeepTools"]) == (Operation, IsKept)


def TestBodyStates() -> None:
    _, Stages = SolvePart(FamilySpec(KBodyCases["CombineJoin"][0]))
    assert [Stage.StateId for Stage in Stages] == [4, 5, 6]
    assert [Stage.Operations for Stage in Stages] == [
        (300, 301, 302),
        (303, 304, 305),
        (306,),
    ]
    _, Stages = SolvePart(FamilySpec(KBodyCases["SplitYZ"][0]))
    assert [Stage.StateId for Stage in Stages] == [4, 4, 5]
    assert [Stage.Operations for Stage in Stages] == [(300, 301, 302), (303,), (304,)]
    _, Stages = SolvePart(FamilySpec(KBodyCases["BodyRectPattern"][0]))
    assert [Stage.Operations for Stage in Stages] == [
        (300, 301, 302),
        (303, 304, 305, 306, 307, 308),
    ]


def TestBodyLimit() -> None:
    Features = (KCube, BodyGridSpec(1, 8, 15.0, 2, 20.0))
    _, Stages = SolvePart(FamilySpec(Features))
    assert len(Stages[-1].Shown) == 16
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    assert len(PartRecords(Model, "Body")) == 16


KBodyRejects: tuple[tuple[KPartFeature, ...], ...] = (
    (KBlock, CombineSpec(1, (2,))),
    (KBlock, KPost, CombineSpec(1, (1,))),
    (KBlock, KPost, CombineSpec(1, (2, 2))),
    (KBlock, KPost, CombineSpec(1, ())),
    (KBlock, KPost, CombineSpec(1, (2,)), CombineSpec(2, (1,))),
    (KBlock, DraftSpec(5.0, "Side draft"), KPost, CombineSpec(1, (2,))),
    (KBlock, KPost, CombineSpec(17, (2,))),
    (KBlock, KPost, CombineSpec(0, (2,))),
    (KBlock, SplitSpec(0)),
    (KBlock, SplitSpec(2), PlaneSpec(20.0, "yz")),
    (KBlock, PlaneSpec(50.0, "yz"), SplitSpec(1)),
    (KBlock, PlaneSpec(30.0, "xy"), SplitSpec(1)),
    (KBlock, PlaneSpec(20.0, "yz"), SplitSpec(1, 2)),
    (KBlock, DraftSpec(5.0, "Side draft"), PlaneSpec(20.0, "yz"), SplitSpec(2)),
    (KBlock, PlaneSpec(20.0, "yz"), SplitSpec(1), FilletSpec((40.0, 30.0), 3.0)),
    (KBlock, KPost, HoleSpec((20.0, 15.0), 6.0)),
    (KBlock, KPost, ExtrudeSpec((CircleCurve((40.0, 30.0), 4.0),), 30.0, "join")),
    (KCube, BodyGridSpec(1, 1, 15.0)),
    (KCube, BodyGridSpec(1, 9, 15.0, 2, 20.0)),
    (KCube, BodyGridSpec(1, 3, -15.0)),
    (KCube, BodyRingSpec(1, 3, 400.0)),
    (KCube, BodyRingSpec(2, 3)),
)


@MarkTests.parametrize("Features", KBodyRejects)
def TestBodyReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(FamilySpec(Features))


@MarkTests.parametrize(
    "Features",
    (
        (ExtrudeSpec((CircleCurve((60.0, 15.0), 5.0),), 20.0),),
        (PlaneSpec(20.0, "yz"), SplitSpec(0)),
    ),
)
def TestBodyCuboid(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(
            DocumentSpec("Cuboid", "height", 20.0, "cuboid", Features=Features)
        )
