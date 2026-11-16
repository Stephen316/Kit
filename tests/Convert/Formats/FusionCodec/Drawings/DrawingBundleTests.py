from dataclasses import replace as ReplaceValue

from pytest import raises as ExpectError

from convert.Formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.Formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph
from convert.Formats.Fusion.BundleCodec.Model.BundleLink import BundleLink
from convert.Formats.Fusion.BundleCodec.Model.BundleModel import BundleModel
from convert.Formats.Fusion.BundleCodec.Model.BundleObject import BundleObject
from convert.Formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs
from convert.Formats.Fusion.BundleCodec.Model.BundleText import BundleText
from convert.Formats.Fusion.BundleCodec.Model.FusionBundle import FusionBundle
from convert.Formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle
from convert.Formats.Fusion.DrawingCodec.Bundle.EmitDrawBundle import EmitDrawBundle
from convert.Formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import ReadDrawBundle
from convert.Formats.Fusion.DrawingCodec.Bundle.RouteBundle import RouteBundle
from convert.Formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.Formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.Formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.Formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout
from convert.Formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing
from tests.Convert.Formats.FusionCodec.Bundles.BundleSource import BundleSource
from tests.Convert.Formats.FusionCodec.Drawings.DrawingSource import (
    DrawingSources,
    FrameReplay,
    HistoricBundle,
)

# the bundle layout cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KBundleLayout = EntryLayout(8, 0x0808, 0x6000, 0x5B6C, 20, 20, 0)

# the storage cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KStorage = "urn:adsk.objects:os.object:wip.dm.prod/"

# design path needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KDesignPath = "00000000-0000-4000-8000-0000000000d3.f3d"

# drawing path needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KDrawingPath = "00000000-0000-4000-8000-0000000000d2.f2d"

# the stranger role cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KStrangerRole = "00000000-0000-4000-8000-0000000000aa"


# shared kit bundle setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def KitBundle(Drawing: FusionDrawing, Source: bytes, RoleText: str) -> DrawingBundle:
    Properties = dict(Drawing.Root.References[0].Properties)
    DesignName = Properties["toDocDisplayName"]
    Design = BundleObject(
        2,
        1,
        Properties["URL"],
        Properties["LineageUrn"],
        KStorage + KDesignPath,
        KDesignPath,
        KDesignPath,
        DesignName,
        DesignName + ".f3d",
        "f3d",
        (),
        (),
        None,
    )
    Fields = (BundleText("neutronRole", RoleText), BundleText("neutronData", ""))
    Relation = BundleRefs("DERIVED", (2,), (BundleLink(2, Fields),))
    Lineage = "urn:adsk.wipprod:dm.lineage:KitFixtureDrawingLineag"
    RootName = Drawing.Root.DocumentName
    RootValue = BundleObject(
        1,
        1,
        "urn:adsk.wipprod:fs.file:vf.KitFixtureDrawingLineag?version=1",
        Lineage,
        KStorage + KDrawingPath,
        KDrawingPath,
        KDrawingPath,
        RootName,
        RootName + ".f2d",
        "f2d",
        (Relation,),
        (),
        None,
    )
    Graph = BundleGraph("2026-11-12T00:00:00+0000", "wipdm", (1,), (Design, RootValue))
    Model = BundleModel("0", RootName, "1", Graph, KDrawingPath)
    Names = ("Manifest.json", "DesignDescription.json", KDesignPath, KDrawingPath)
    Layout = tuple(PackageSlot(NameValue, KBundleLayout) for NameValue in Names)
    return DrawingBundle(Model, Drawing, (BundleFile(KDesignPath, Source),), Layout)


# the kit bundle contract needs boundary coverage so stored document relationships remain consistent
def TestKitBundle() -> None:
    Sources = DrawingSources()
    Replay = FrameReplay()
    Drawing = ReadDrawing(Sources["A1Dimension"], Replay.Inflate)
    RoleText = Drawing.Root.References[0].Role
    Bundle = KitBundle(Drawing, Sources["Source"], RoleText)
    DataValue = EmitDrawBundle(Bundle, Replay.Compress)
    Routed = RouteBundle(DataValue, Replay.Inflate)
    assert isinstance(Routed, DrawingBundle) and Routed == Bundle
    assert EmitDrawBundle(Routed, Replay.Compress) == DataValue
    Stranger = KitBundle(Drawing, Sources["Source"], KStrangerRole)
    with ExpectError(ValueError, match="disagree with the bundle graph"):
        _ = EmitDrawBundle(Stranger, Replay.Compress)


# the design route contract needs boundary coverage so stored document relationships remain consistent
def TestDesignRoute() -> None:
    assert isinstance(RouteBundle(BundleSource().read_bytes()), FusionBundle)


# the historic contract needs boundary coverage so stored document relationships remain consistent
def TestHistoric() -> None:
    DataValue = HistoricBundle()
    Bundle = ReadDrawBundle(DataValue)
    Drawing = Bundle.Drawing
    assert Drawing.Asset.Version == 10 and Drawing.Root.SaveLabel is None
    assert all(isinstance(Segment, LegacySegment) for Segment in Drawing.Segments)
    assert Drawing.Redirections is not None and Drawing.Database is not None
    assert Drawing.Database.Content.startswith(b"AC1027")
    assert len(Bundle.Documents) == 3
    assert EmitDrawBundle(Bundle) == DataValue
    assert RouteBundle(DataValue) == Bundle
    Altered = ReplaceValue(Bundle, Documents=Bundle.Documents[1:])
    with ExpectError(ValueError, match="disagree with design graph"):
        _ = EmitDrawBundle(Altered)
