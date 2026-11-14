from typing import cast as CastValue

from pytest import approx as ApproxValue, mark as MarkTests

from convert.adapters.Fusion import MakeFusionDoc
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.enums.EnumFeatures import FeatureKind
from tests.convert.formats.FusionCodec.Documents.PartFeatures.NativeControl import (
    NativeControl,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KPartCases,
    PartSpec,
)

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
