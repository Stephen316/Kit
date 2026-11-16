from pytest import approx as ApproxValue, mark as MarkTests, raises as RaisesError

from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import (
    MeasurePart,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CombineSpec import (
    CombineSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PasteSpec import (
    PasteSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.SweepSpec import (
    SweepSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Pattern.MoveSlab import (
    ShiftLabel,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import (
    AuthorSchemas,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.BulletinRefs import (
    IsIdentityRef,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    KBlock,
    KPocket,
    FamilySpec,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.NativeControl import (
    NativeBodies,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)

# the paste guid cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPasteGuid = "BA3059E4-4B23-4D02-9D18-E7BB95C991F3"

# the side post cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSidePost = ExtrudeSpec(
    (CircleCurve((60.0, 15.0), 5.0),),
    20.0,
    "new",
    "one",
    0.0,
    "Post sketch",
    "Post extrude",
)

# the corner post cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KCornerPost = ExtrudeSpec(
    (CircleCurve((40.0, 30.0), 10.0),),
    20.0,
    "new",
    "one",
    0.0,
    "Post sketch",
    "Post extrude",
)

# the round cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRound = FilletSpec((40.0, 30.0), 3.0, "Corner round")

# the paste cases cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPasteCases: dict[str, tuple[KPartFeature, ...]] = {
    "PastePlain": (KBlock, PasteSpec(1, "Body paste")),
    "PasteFillet": (KBlock, KRound, PasteSpec(1, "Body paste")),
    "PasteTwice": (KBlock, PasteSpec(1, "First paste"), PasteSpec(1, "Second paste")),
    "PasteSecond": (KBlock, KSidePost, PasteSpec(2, "Post paste")),
    "PastePocket": (KBlock, KPocket, PasteSpec(1, "Body paste")),
    "PasteCombine": (
        KBlock,
        KCornerPost,
        PasteSpec(2, "Post paste"),
        CombineSpec(1, (3,), "cut", False, "Body combine"),
    ),
}

# the native cases cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KNativeCases = ("PastePlain", "PasteFillet", "PasteTwice", "PasteSecond")

# bend path needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KBendPath = (
    LineCurve((0.0, 0.0), (0.0, 20.0)),
    ArcCurve((-30.0, 20.0), 30.0, 0.0, 90.0),
)


# the paste solid contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("NameValue", KNativeCases)
def TestPasteSolid(NameValue: str) -> None:
    _, Stages = SolvePart(FamilySpec(KPasteCases[NameValue]))
    Final = Stages[-1]
    Shown = [Solid for Solid in Final.Bodies if Solid.Ordinal in Final.Shown]
    Native = NativeBodies(NameValue)
    assert len(Shown) == len(Native)
    for Solid, Observed in zip(Shown, Native):
        Measured = MeasurePart(Solid)
        assert (Measured.FaceCount, Measured.EdgeCount) == (
            Observed["faces"],
            Observed["edges"],
        )
        assert Measured.VolumeCm == ApproxValue(Observed["volume_cm3"], rel=1e-7)
        assert Measured.AreaCm == ApproxValue(Observed["area_cm2"], rel=1e-7)


# the paste labels contract needs boundary coverage so stored document relationships remain consistent
def TestPasteLabels() -> None:
    _, Stages = SolvePart(FamilySpec(KPasteCases["PasteFillet"]))
    Stage = Stages[-1]
    assert Stage.Operations == (304, 305)
    Source, Pasted = Stage.Before, Stage.After
    assert Pasted.Ordinal == 2
    assert Pasted.BodyLabel == FaceLabel("304", (), 1)
    for Lower, Upper in zip(Source.Slabs, Pasted.Slabs, strict=True):
        assert Upper.FloorLabel == ShiftLabel(Lower.FloorLabel, (304,))
        assert Upper.RoofLabel == ShiftLabel(Lower.RoofLabel, (304,))
        for First, Second in zip(Lower.Loops, Upper.Loops, strict=True):
            assert [SpanValue.Label for SpanValue in Second] == [
                ShiftLabel(SpanValue.Label, (304,)) for SpanValue in First
            ]
    assert [RimLabel for _, _, RimLabel in Pasted.EdgeTags] == [
        RimLabel for _, _, RimLabel in Source.EdgeTags
    ]


# the paste saved contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("NameValue", tuple(KPasteCases))
def TestPasteSaved(NameValue: str) -> None:
    Features = KPasteCases[NameValue]
    _, Stages = SolvePart(FamilySpec(Features))
    Final = Stages[-1]
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    assert ReadDocument(EmitParsed(Model)) == Model
    Pastes = sum(isinstance(Feature, PasteSpec) for Feature in Features)
    assert len(PartRecords(Model, "DcPasteBodies")) == Pastes
    assert len(PartRecords(Model, "DcBaseFeature")) == Pastes
    assert len(PartRecords(Model, "BodyUuidProgenitor")) == Pastes
    Bodies = PartRecords(Model, "Body")
    assert len(Bodies) == len(Final.Bodies) + Pastes
    Hidden = [Fields for Fields in Bodies if not Fields["isVisible"]]
    assert len(Hidden) == Pastes + len(Final.Bodies) - len(Final.Shown)
    for Fields in PartRecords(Model, "DcBaseFeature"):
        assert Fields["isAssociative"] is True
        assert Fields["featureBaseName"] == "Base Feature"
    for Fields in PartRecords(Model, "DcPasteBodies"):
        assert (Fields["startModelHS"], Fields["endModelHS"]) == (-1, -1)
        assert Fields["featureBaseName"] == "CopyPasteBodies"
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert IsIdentityRef(History)


# the paste scope contract needs boundary coverage so stored document relationships remain consistent
def TestPasteScope() -> None:
    Plain = {
        Schema.Value.ClassGuid.upper() for Schema in AuthorSchemas("part", False, True)
    }
    Pasted = {
        Schema.Value.ClassGuid.upper()
        for Schema in AuthorSchemas("part", False, True, True)
    }
    assert KPasteGuid not in Plain
    assert KPasteGuid in Pasted


# the paste rejects cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPasteRejects: tuple[tuple[KPartFeature, ...], ...] = (
    (KBlock, PasteSpec(2)),
    (KBlock, PasteSpec(0)),
    (KBlock, PasteSpec(17)),
    (KBlock, KCornerPost, CombineSpec(1, (2,)), PasteSpec(2)),
    (SweepSpec(KBendPath, -5.0, 5.0, 0.0, 10.0), PasteSpec(1)),
    (KBlock, PasteSpec(1, "")),
)


# the paste reject contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("Features", KPasteRejects)
def TestPasteReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(FamilySpec(Features))
