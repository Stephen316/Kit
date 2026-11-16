from tests.Convert.Formats.FusionCodec.Containers.CheckSubjects import (
    CheckSubjects,
)
from dataclasses import replace as Replace
from pathlib import Path as FilePath

from pytest import raises as RaiseError

from convert.Formats.Fusion.ContainerCodec.Assembly.BuildAssembly import BuildAssembly
from convert.Formats.Fusion.ContainerCodec.Browser.BuildBrowser import BuildBrowser
from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.DocumentCodec.BuildDesign import BuildDesign
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.Convert.Formats.FusionCodec.Containers.FindEntityField import FindEntityField
from tests.Convert.Formats.FusionCodec.Containers.MakeContainer import MakeContainer
from tests.Convert.Formats.FusionCodec.Containers.ReadAuxiliary import ReadAuxiliary

# the instance rev cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KInstanceRev = "31415926-1111-4222-8333-0123456789ab"


# the aux archive contract needs boundary coverage so stored document relationships remain consistent
def TestAuxArchive(TmpPath: FilePath) -> None:
    Envelope = MakeContainer()
    Specification = DocumentSpec(
        "Independent assembly", "spanLength", 26.75, "circle", 9.25
    )
    Design = BuildDesign(Specification, Envelope.Asset.AssetId)
    Assembly = BuildAssembly(
        Design, Specification.Title, Envelope.Asset.SnapshotId, KInstanceRev
    )
    Browser = BuildBrowser(Design, Assembly)
    Value = Replace(
        Envelope, Streams=(Design.Streams, Assembly.Streams, Browser.Streams)
    )
    Target = TmpPath / "IndependentAssembly.f3d"
    _ = Target.write_bytes(EmitContainer(Value))
    Decoded = ReadContainer(Target.read_bytes())
    ActRecords = ReadAuxiliary(Decoded.Streams[1], Assembly.Profile, SegmentKind.KAct)
    BrowserRows = ReadAuxiliary(
        Decoded.Streams[2], Browser.Profile, SegmentKind.KBrowser
    )
    assert ActRecords == Assembly.Records
    assert BrowserRows == Browser.Records
    assert len(ActRecords) == 8
    assert len(BrowserRows) == 33
    assert FindEntityField(ActRecords, 103, "AssetRevGuid") == Envelope.Asset.SnapshotId
    assert FindEntityField(ActRecords, 103, "RevisionGuid") == Design.RevisionId
    assert FindEntityField(ActRecords, 100, "designComponent") == SegmentRef(
        Design.Roles["component"], 0
    )
    assert FindEntityField(ActRecords, 100, "rParent") == LocalRef(102)
    for Identity in range(210, 215):
        assert FindEntityField(BrowserRows, Identity, "entity") == SegmentRef(
            Design.Roles["constraints"], 0
        )
    CheckSubjects(BrowserRows, Design.Roles)
    assert FindEntityField(BrowserRows, 228, "entity") == SegmentRef(
        Design.Roles["units"], 0
    )
    assert FindEntityField(BrowserRows, 201, "ACTInstance") == SegmentRef(102, 1)
    assert len([Entry for Entry in BrowserRows if Entry.ObjectId == 200]) == 2


# the wrong roles contract needs boundary coverage so stored document relationships remain consistent
def TestWrongRoles(TmpPath: FilePath) -> None:
    Envelope = MakeContainer()
    Specification = DocumentSpec("Invalid assembly", "spanLength", 12.25, "parameter")
    Design = BuildDesign(Specification, Envelope.Asset.AssetId)
    Assembly = BuildAssembly(
        Design, Specification.Title, Envelope.Asset.SnapshotId, KInstanceRev
    )
    Invalid = Replace(
        Design, Roles=Design.Roles | {"constraints": Design.Roles["relationships"]}
    )
    Target = TmpPath / "WrongRole.f3d"
    with RaiseError(ValueError, match="incompatible design target"):
        Browser = BuildBrowser(Invalid, Assembly)
        _ = Target.write_bytes(
            EmitContainer(
                Replace(
                    Envelope,
                    Streams=(Design.Streams, Assembly.Streams, Browser.Streams),
                )
            )
        )
    assert not Target.exists()
