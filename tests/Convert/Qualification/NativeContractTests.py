from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.json.Adapter import JsonAdapter
from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    FamilySpec,
    KBlock,
)
from tests.Convert.Qualification.RejectPublic import RejectPublic


# writer contracts must reject unqualified history without blocking confirmed authoring
def TestContract(TmpPath: FilePath) -> None:
    Document = AdapterCase("cuboid")
    assert all(
        StepValue.kind != FeatureKind.NATIVE for StepValue in Document.feature_timeline
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


# portable graph mismatches must be diagnosed before native writing changes the destination
@TestMark.parametrize("ModeValue", ("graph", "version"))
def TestBadContract(TmpPath: FilePath, ModeValue: str) -> None:
    Document = AdapterCase("cuboid")
    Document = ReplaceData(
        Document,
        feature_timeline=Document.feature_timeline[:-1]
        + (
            ReplaceData(
                Document.feature_timeline[-1], kind=FeatureKind.NATIVE, definition=None
            ),
        ),
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


# native fusion readback needs enough feature state for public writing to assess completeness
def TestPartState(TmpPath: FilePath) -> None:
    Specification = FamilySpec((KBlock, MoveSpec((5.0, 5.0, 2.0), "Body turn", 30.0)))
    TargetPath = TmpPath / "CodecFamily.f3d"
    _ = TargetPath.write_bytes(EmitDocument(Specification))
    assert len(ReadDocument(TargetPath.read_bytes()).Bodies) == 1
    with RaisesError(ValueError, match="Unsupported Fusion semantic-state value"):
        _ = MakeFusionDoc(Specification)
