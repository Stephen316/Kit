from collections import Counter

from pytest import approx as ApproxValue, mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import (
    MeasurePart,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import (
    PlaneSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from tests.convert.formats.FusionCodec.Documents.PartFeatures.BulletinRefs import (
    IsIdentityRef,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    KBlock,
    KFamilyCases,
    KFamilyNames,
    KPocket,
    FamilySpec,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.NativeControl import (
    NativeControl,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)


@MarkTests.parametrize("NameValue", tuple(KFamilyCases))
def TestFamilySolid(NameValue: str) -> None:
    Features, Volume, Faces, Edges = KFamilyCases[NameValue]
    _, Stages = SolvePart(FamilySpec(Features))
    Measured = MeasurePart(Stages[-1].After)
    assert (Measured.FaceCount, Measured.EdgeCount) == (Faces, Edges)
    assert Measured.VolumeCm == ApproxValue(Volume, abs=1e-6)


@MarkTests.parametrize(
    "NameValue",
    (
        "RectPattern",
        "FeatureCircPattern",
        "MirrorFeature",
        "ChamferTwoDistances",
        "ChamferDistanceAngle",
        "FilletTwoEdges",
        "ChamferTwoEdges",
        "ConstructionSet",
    ),
)
def TestFamNative(NameValue: str) -> None:
    _, Stages = SolvePart(FamilySpec(KFamilyCases[NameValue][0]))
    Measured = MeasurePart(Stages[-1].After)
    Native = NativeControl(NameValue)
    assert (Measured.FaceCount, Measured.EdgeCount) == (
        Native["faces"],
        Native["edges"],
    )
    assert Measured.VolumeCm == ApproxValue(Native["volume_cm3"], rel=1e-7)
    assert Measured.AreaCm == ApproxValue(Native["area_cm2"], rel=1e-7)


@MarkTests.parametrize("NameValue", tuple(KFamilyCases))
def TestFamArchive(NameValue: str) -> None:
    Features = KFamilyCases[NameValue][0]
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    assert ReadDocument(EmitParsed(Model)) == Model
    Expected = Counter(KFamilyNames[type(Feature)] for Feature in Features)
    for ClassName, Count in Expected.items():
        assert len(PartRecords(Model, ClassName)) == Count
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    Copies = sum(
        isinstance(Feature, (PatternSpec, CircularSpec, MirrorSpec))
        for Feature in Features
    )
    Tracks = [Entity for Entity in History.Entities if isinstance(Entity, TrackAttrib)]
    assert bool(Tracks) == bool(Copies)
    assert IsIdentityRef(History)


def TestPlaneState() -> None:
    _, Stages = SolvePart(FamilySpec(KFamilyCases["MirrorFeature"][0]))
    assert [Stage.StateId for Stage in Stages] == [4, 5, 5, 6]
    assert [Stage.Operations for Stage in Stages] == [
        (300, 301, 302),
        (303, 304, 305),
        (306,),
        (307, 308),
    ]
    Model = ReadDocument(EmitDocument(FamilySpec(KFamilyCases["MirrorFeature"][0])))
    Planes = PartRecords(Model, "DcWorkPlane")
    assert [(Fields["startModelHS"], Fields["endModelHS"]) for Fields in Planes] == [
        (-1, -1)
    ]


KRejected: tuple[tuple[KPartFeature, ...], ...] = (
    (KBlock, PatternSpec(0, 3, 12.0)),
    (KBlock, KPocket, PatternSpec(1, 1, 12.0)),
    (KBlock, KPocket, PatternSpec(1, 3, -12.0)),
    (KBlock, KPocket, PatternSpec(1, 65, 1.0)),
    (KBlock, KPocket, CircularSpec(1, 1)),
    (KBlock, KPocket, CircularSpec(1, 3, 400.0)),
    (KBlock, KPocket, PatternSpec(3, 2, 12.0)),
    (KBlock, KPocket, PlaneSpec(20.0, "xy"), MirrorSpec(1, 2)),
    (KBlock, KPocket, MirrorSpec(1, 1)),
    (KBlock, PlaneSpec(float("inf"))),
    (KBlock, HoleSpec((20.0, 15.0), 8.0, 25.0)),
    (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Bevel", 2.0, 30.0)),
    (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Bevel", 0.0, 90.0)),
    (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Bevel", -2.0)),
    (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Bevel", 45.0)),
    (KBlock, FilletSpec((40.0, 30.0), 3.0, "Rounds", ((40.0, 30.0),))),
    (KBlock, ChamferSpec((40.0, 30.0), 3.0, MoreCornersMm=((20.0, 30.0),))),
    (KBlock, AxisSpec((20.0, 30.0))),
    (KBlock, AxisSpec((40.0, 30.0), "")),
    (KBlock, PointSpec((40.0, float("nan")))),
)


@MarkTests.parametrize("Features", KRejected)
def TestFamReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(FamilySpec(Features))


KHolePlaces: tuple[tuple[str, int, tuple[float, float]], ...] = (
    ("HoleFlat", 6, (0.0, 0.0)),
    ("MultiPocketPart", 17, (-1.2, -0.7)),
    ("MultiDiscPart", 6, (0.0, 0.0)),
)


@MarkTests.parametrize(("NameValue", "PointKind", "Offsets"), KHolePlaces)
def TestHolePlace(NameValue: str, PointKind: int, Offsets: tuple[float, float]) -> None:
    Model = ReadDocument(EmitDocument(FamilySpec(KFamilyCases[NameValue][0])))
    Fields = PartRecords(Model, "DRPoint")[0]
    Plane = Fields["param"]
    assert isinstance(Plane, ValueStruct)
    assert Fields["refType"] == PointKind
    assert tuple(Entry.Value for Entry in Plane.Fields) == ApproxValue(Offsets)
    Recipes = [Entry["m_Recipe"] for Entry in PartRecords(Model, "ASMRecipe")]
    Bounded = [
        Entry.Value.Payload
        for Entry in Recipes
        if isinstance(Entry, OptionalValue)
        and isinstance(Entry.Value, RecipeValue)
        and isinstance(Entry.Value.Payload, BoundFaceRecipe)
    ]
    assert Bounded
    for Payload in Bounded:
        for EdgeValue in Payload.Edges:
            for Corner in EdgeValue.AdjacentVertices:
                Faces = [
                    FaceValue.PrimaryTagIndex for FaceValue in Corner.AdjacentFaces
                ]
                assert len(Faces) == len(set(Faces))
