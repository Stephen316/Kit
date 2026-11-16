from typing import cast as CastValue

from pytest import approx as ApproxValue, mark as MarkTests

from convert.adapters.Fusion import MakeFusionDoc
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.NativeControl import (
    NativeControl,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KPartCases,
    PartSpec,
)

# the kinds cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KKinds = {
    "Fillet": (FeatureKind.KFillet,),
    "Chamfer": (FeatureKind.KChamfer,),
    "Shell": (FeatureKind.KShell,),
    "FilletShell": (FeatureKind.KFillet, FeatureKind.KShell),
    "MultiFeature": (
        FeatureKind.KFillet,
        FeatureKind.KChamfer,
        FeatureKind.KFillet,
        FeatureKind.KShell,
    ),
}


# the part adapter contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("NameValue", tuple(KPartCases))
def TestPartAdapter(NameValue: str) -> None:
    SpecValue = PartSpec(NameValue)
    Document = MakeFusionDoc(SpecValue)
    Document.AssertValid()
    Steps = Document.feature_timeline[2:]
    assert tuple(StepValue.kind for StepValue in Steps) == KKinds[NameValue]
    assert [StepValue.order for StepValue in Steps] == list(range(2, 2 + len(Steps)))
    Contract = CastValue(dict[str, object], Document.metadata["fusion.authoring"])
    assert DecodeState(Contract["spec"]) == SpecValue
    assert Document.bodies[0].final_feature_id == Steps[-1].id
    _ = ReadDocument(EncodeDocument(Document))


# the part counts contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("NameValue", ("Fillet", "Chamfer", "Shell"))
def TestPartCounts(NameValue: str) -> None:
    Counts = MakeFusionDoc(PartSpec(NameValue)).bodies[0].topology
    Native = NativeControl(NameValue)
    assert Counts is not None
    assert (Counts.face_count, Counts.edge_count, Counts.vertex_count) == (
        Native["faces"],
        Native["edges"],
        Native["vertices"],
    )
    Volume = CastValue(float, Native["volume_cm3"])
    assert Counts.volume == ApproxValue(1000.0 * Volume, rel=1e-7)
