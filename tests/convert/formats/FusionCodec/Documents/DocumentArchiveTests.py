from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from typing import Literal

from pytest import approx as ApproxValue
from pytest import mark as MarkTests
from pytest import raises as RaisesError

from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.NamedGroups import NamedGroups
from tests.convert.formats.FusionCodec.Documents.RenameFeature import RenameFeature


@MarkTests.parametrize("ProfileKind", ("parameter", "circle", "extrusion"))
def TestDocProfiles(
    TmpPath: FilePath, ProfileKind: Literal["parameter", "circle", "extrusion"]
) -> None:
    SpecValue = DocumentSpec(
        "Native archive integration", "driveLength", 29.75, ProfileKind, 8.25
    )
    Source = TmpPath / "Authored.f3d"
    _ = Source.write_bytes(EmitDocument(SpecValue))
    Model = ReadDocument(Source.read_bytes())
    Parameters = NamedGroups(Model, "Parameter")
    Parameter = next(
        Entry for Entry in Parameters if Entry["userName"] == "driveLength"
    )
    assert Parameter["value"] == ApproxValue(2.975)
    assert Parameter["expression"] == "29.75 mm"
    assert len(NamedGroups(Model, "MSketch")) == int(ProfileKind != "parameter")
    assert len(NamedGroups(Model, "DcExtrudeFeature")) == int(
        ProfileKind == "extrusion"
    )
    assert len(Model.Bodies) == int(ProfileKind == "extrusion")
    if ProfileKind == "extrusion":
        BodyValue = Model.Bodies[0].History
        assert isinstance(BodyValue, HistoryModel)
        assert BodyValue.Model.Radius == ApproxValue(8.25)
        assert BodyValue.Model.Height == ApproxValue(29.75)
        assert BodyValue.Model.BasePoint == (0.0, 0.0, 0.0)
        assert (
            next(Entry for Entry in Parameters if Entry["name"] == "AlongDistance")[
                "expression"
            ]
            == "driveLength"
        )
        Feature = next(
            Entry
            for Entry in NamedGroups(Model, "DcFeature")
            if Entry["featureBaseName"] == "Extrude"
        )
        assert Feature["startModelHS"] == BodyValue.History.InitialId
        assert Feature["endModelHS"] == BodyValue.History.CurrentId
    Target = TmpPath / "Reemitted.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened.Segments == Model.Segments
    assert Reopened.Bodies == Model.Bodies


def TestParsedEdit(TmpPath: FilePath) -> None:
    Source = TmpPath / "Source.f3d"
    _ = Source.write_bytes(
        EmitDocument(DocumentSpec("Edit archive", "heightValue", 17.25))
    )
    Model = ReadDocument(Source.read_bytes())
    Target = TmpPath / "Renamed.f3d"
    _ = Target.write_bytes(EmitParsed(RenameFeature(Model, "Edited typed feature")))
    Reopened = ReadDocument(Target.read_bytes())
    assert {
        Entry["featureUserName"] for Entry in NamedGroups(Reopened, "DcFeature")
    } == {"Edited typed feature"}
    assert Reopened.Bodies == Model.Bodies
    assert NamedGroups(Reopened, "Parameter") == NamedGroups(Model, "Parameter")


def TestUnknownPart(TmpPath: FilePath) -> None:
    Source = EmitDocument(
        DocumentSpec("Unsupported part", "heightValue", 12.0, "parameter")
    )
    Container = ReadContainer(Source)
    Changed = ReplaceValue(
        Container, Parts=(ContainerPart("Images.BlobParts/Unknown.bin", b"unknown"),)
    )
    Target = TmpPath / "Unsupported.f3d"
    _ = Target.write_bytes(EmitContainer(Changed))
    with RaisesError(ValueError, match="Unsupported Fusion document part"):
        _ = ReadDocument(Target.read_bytes())


def TestHeaderGuard(TmpPath: FilePath) -> None:
    Source = TmpPath / "Source.f3d"
    _ = Source.write_bytes(
        EmitDocument(DocumentSpec("Header guard", "heightValue", 12.0))
    )
    Model = ReadDocument(Source.read_bytes())
    BodyValue = Model.Bodies[0]
    Header = ReplaceValue(BodyValue.History.Header, Scale=10.0)
    Changed = ReplaceValue(
        BodyValue, History=ReplaceValue(BodyValue.History, Header=Header)
    )
    with RaisesError(ValueError, match="Unsupported Fusion document BRep header"):
        _ = EmitParsed(ReplaceValue(Model, Bodies=(Changed,)))
