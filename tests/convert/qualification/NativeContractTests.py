from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.json.Adapter import JsonAdapter
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.enums.EnumFeatures import FeatureKind
from tests.convert.formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    FamilySpec,
    KBlock,
)
from tests.convert.qualification.RejectPublic import RejectPublic


def TestContract(TmpPath: FilePath) -> None:
    Document = MakeFusionDoc(
        FamilySpec((KBlock, MoveSpec((5.0, 5.0, 2.0), "Body turn", 30.0)))
    )
    assert any(
        StepValue.kind == FeatureKind.NATIVE and StepValue.definition is None
        for StepValue in Document.feature_timeline
    )
    JsonPath = TmpPath / "Qualified.json"
    _ = JsonAdapter().write(Document, JsonPath)
    Reopened = OpenDocument(JsonPath)
    assert Reopened.feature_timeline == Document.feature_timeline
    FusionPath = TmpPath / "Qualified.f3d"
    _ = WriteDocument(
        Reopened, FusionPath, destination_format="f3d", allow_carrier=False
    )
    assert len(ReadDocument(FusionPath.read_bytes()).Bodies) == 1


@TestMark.parametrize("ModeValue", ("graph", "version"))
def TestBadContract(TmpPath: FilePath, ModeValue: str) -> None:
    Document = MakeFusionDoc(
        FamilySpec((KBlock, MoveSpec((5.0, 5.0, 2.0), "Body turn", 30.0)))
    )
    if ModeValue == "version":
        Document = ReplaceData(
            Document, metadata={"fusion.authoring": {"version": 99, "spec": {}}}
        )
    else:
        Document = ReplaceData(
            Document,
            feature_timeline=tuple(
                (
                    ReplaceData(StepValue, name="Changed outside contract")
                    if StepValue.kind == FeatureKind.NATIVE
                    else StepValue
                )
                for StepValue in Document.feature_timeline
            ),
        )
    RejectPublic(Document, TmpPath)
