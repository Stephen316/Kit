from math import inf as KInfinity, nan as KNotNumber
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
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    KProfileCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
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

KLower = RectCurves((0.0, 0.0), (40.0, 30.0))
KUpper = RectCurves((10.0, 10.0), (30.0, 20.0))
KLoftRects = LoftSpec(KLower, KUpper, 30.0, FeatureName="Block loft")
KLoftCircles = LoftSpec(
    (CircleCurve((0.0, 0.0), 10.0),),
    (CircleCurve((0.0, 0.0), 5.0),),
    30.0,
    FeatureName="Cone loft",
)
KWedge = LoftSpec(
    RectCurves((50.0, 0.0), (90.0, 30.0)),
    RectCurves((55.0, 20.0), (75.0, 25.0)),
    25.0,
    "Wedge base",
    "Wedge plane",
    "Wedge top",
    "Wedge loft",
)
KLoftCases: dict[str, tuple[KPartFeature, ...]] = {
    "LoftRects": (KLoftRects,),
    "LoftCircles": (KLoftCircles,),
    "LoftWedgeBody": (KBlock, KWedge),
}


@MarkTests.parametrize("NameValue", ("LoftRects", "LoftCircles"))
def TestLoftSolid(NameValue: str) -> None:
    _, Stages = SolvePart(FamilySpec(KLoftCases[NameValue]))
    (Observed,) = NativeBodies(NameValue)
    Measured = MeasurePart(Stages[-1].After)
    assert (Measured.FaceCount, Measured.EdgeCount) == (
        Observed["faces"],
        Observed["edges"],
    )
    assert Measured.VolumeCm == ApproxValue(Observed["volume_cm3"], rel=1e-7)
    assert Measured.AreaCm == ApproxValue(Observed["area_cm2"], rel=1e-7)


def TestLoftWedge() -> None:
    _, Stages = SolvePart(FamilySpec(KLoftCases["LoftWedgeBody"]))
    Final = Stages[-1]
    assert Final.Shown == (1, 2)
    Block, Wedge = (MeasurePart(Solid) for Solid in Final.Bodies)
    assert Block.VolumeCm == ApproxValue(24.0, rel=1e-9)
    Middle = 30.0 * 17.5
    Expected = 25.0 / 6.0 * (1200.0 + 4.0 * Middle + 100.0) / 1000.0
    assert Wedge.VolumeCm == ApproxValue(Expected, rel=1e-9)
    assert (Wedge.FaceCount, Wedge.EdgeCount) == (6, 12)


def TestLoftStages() -> None:
    _, Stages = SolvePart(FamilySpec(KLoftCases["LoftRects"]))
    (Stage,) = Stages
    assert (Stage.Operations, Stage.StateId) == ((300, 301, 302, 303), 4)
    assert Stage.Sketch is not None and Stage.Upper is not None
    assert (Stage.Sketch.Ordinal, Stage.Sketch.NextTag) == (1, 109)
    assert (Stage.Upper.Ordinal, Stage.Upper.NextTag) == (2, 118)
    assert Stage.Upper.LiftCm == 3.0
    _, Stages = SolvePart(FamilySpec(KLoftCases["LoftWedgeBody"]))
    assert [Stage.Operations for Stage in Stages] == [
        (300, 301, 302),
        (303, 304, 305, 306),
    ]
    assert [Stage.StateId for Stage in Stages] == [4, 5]


@MarkTests.parametrize("NameValue", tuple(KLoftCases))
def TestLoftArchive(NameValue: str) -> None:
    Features = KLoftCases[NameValue]
    LoftValue = CastValue(LoftSpec, Features[-1])
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    assert ReadDocument(EmitParsed(Model)) == Model
    Sketches = len(Features) + 1
    Expected = {
        "DcLoftFeature": 1,
        "DcLoftSectionData": 2,
        "DcLoftToolBody": 1,
        "DcWorkPlane": 1,
        "DcSketch": Sketches,
        "MSketch": Sketches,
        "LoftProgenitor": len(LoftValue.LowerProfile),
        "Body": len(Features),
    }
    for ClassName, Count in Expected.items():
        assert len(PartRecords(Model, ClassName)) == Count
    (Feature,) = PartRecords(Model, "DcLoftFeature")
    assert (Feature["booleanOperation"], Feature["featureUserName"]) == (
        4,
        LoftValue.FeatureName,
    )
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert IsIdentityRef(History)


def TestLoftRecords() -> None:
    Model = ReadDocument(EmitDocument(FamilySpec(KLoftCases["LoftRects"])))
    Tables = [
        Fields
        for Fields in PartRecords(Model, "ProgenitorTable")
        if Fields["tagId"] == 8
    ]
    assert len(Tables) == 1
    (SeedFields,) = PartRecords(Model, "BodyProgenitor")
    assert "Items=(49, 50, 51, 52, 53, 54)" in repr(SeedFields["featureTagOccMap"])
    assert "operationId', Value=303" in repr(SeedFields["featureTagOccMap"])
    Frames = [Fields["transform"] for Fields in PartRecords(Model, "CoordinateSystem")]
    Lifted = Frames[-1]
    assert isinstance(Lifted, MatrixValue) and Lifted.Entries is not None
    assert Lifted.Entries[11] == 3.0
    Names = [Fields["userName"] for Fields in PartRecords(Model, "Sketch")]
    assert Names == ["Loft base", "Loft top"]
    Planes = [Fields["userName"] for Fields in PartRecords(Model, "WorkPlane")]
    assert Planes[-1] == "Loft plane"


def ShiftCurves(Curves: tuple[KProfileCurve, ...]) -> tuple[KProfileCurve, ...]:
    return Curves[1:] + Curves[:1]


KSlot = (
    LineCurve((10.0, 0.0), (30.0, 0.0)),
    ArcCurve((30.0, 10.0), 10.0, -90.0, 180.0),
    LineCurve((30.0, 20.0), (10.0, 20.0)),
    ArcCurve((10.0, 10.0), 10.0, 90.0, 180.0),
)
KTriangle = (
    LineCurve((10.0, 10.0), (30.0, 10.0)),
    LineCurve((30.0, 10.0), (20.0, 20.0)),
    LineCurve((20.0, 20.0), (10.0, 10.0)),
)
KDisc = (CircleCurve((0.0, 0.0), 10.0),)
KLoftRejects: tuple[tuple[KPartFeature, ...], ...] = (
    (LoftSpec(KLower, ShiftCurves(KUpper), 30.0),),
    (LoftSpec(KLower, KTriangle, 30.0),),
    (LoftSpec(KDisc, (CircleCurve((5.0, 0.0), 5.0),), 30.0),),
    (LoftSpec(KDisc, KUpper, 30.0),),
    (LoftSpec(KSlot, KSlot, 30.0),),
    (LoftSpec(KLower, KUpper, 0.0),),
    (LoftSpec(KLower, KUpper, -5.0),),
    (LoftSpec(KLower, KUpper, KNotNumber),),
    (LoftSpec(KLower, KUpper, KInfinity),),
    (LoftSpec(KLower, KUpper, 30.0, PlaneName=""),),
    (LoftSpec(KLower, CastValue(tuple[KProfileCurve, ...], list(KUpper)), 30.0),),
    (KLoftRects, FilletSpec((40.0, 30.0), 3.0)),
    (KBlock, KWedge, CombineSpec(1, (2,))),
    (KBlock, KWedge, CombineSpec(2, (1,))),
)


@MarkTests.parametrize("Features", KLoftRejects)
def TestLoftReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(FamilySpec(Features))


def TestLoftCuboid() -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(
            DocumentSpec("Cuboid", "height", 20.0, "cuboid", Features=(KLoftRects,))
        )
