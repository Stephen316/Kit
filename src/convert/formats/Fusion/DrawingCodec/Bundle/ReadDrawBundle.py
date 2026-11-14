from collections.abc import Callable

from convert.formats.Fusion.BundleCodec.Json.EmitJson import EmitJson
from convert.formats.Fusion.BundleCodec.Json.EmitModel import EmitModel
from convert.formats.Fusion.BundleCodec.Json.ReadModel import ReadModel
from convert.formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.formats.Fusion.DrawingCodec.Bundle.CheckBundle import (
    CheckBundle,
    DrawingObject,
)
from convert.formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.formats.Fusion.DrawingCodec.Package.ReadPackage import ReadPackage
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing

KManifestName = "Manifest.json"

KDescriptionName = "DesignDescription.json"


def ReadDrawBundle(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> DrawingBundle:
    Package = ReadPackage(DataValue, InflateZstd)
    Files = {Entry.Name: Entry.Payload for Entry in Package.Entries}
    if any(NameValue.endswith("/") for NameValue in Files):
        raise ValueError("Fusion drawing bundles do not contain directories")
    Manifest = Files.pop(KManifestName, None)
    Description = Files.pop(KDescriptionName, None)
    if Manifest is None or Description is None:
        raise ValueError("Missing Fusion drawing bundle description")
    Model = ReadModel(Manifest, Description)
    if (
        EmitJson({"root": Model.RootPath}) != Manifest
        or EmitJson(EmitModel(Model)) != Description
    ):
        raise ValueError("Fusion drawing bundle description is not canonical")
    RootValue = DrawingObject(Model)
    Drawing = ReadDrawing(Files.pop(RootValue.MemberPath), InflateZstd)
    CheckBundle(Model, Drawing)
    Documents = tuple(
        BundleFile(Entry.MemberPath, Files.pop(Entry.MemberPath))
        for Entry in Model.Graph.Objects
        if Entry.ObjectId != RootValue.ObjectId
    )
    if Files:
        raise ValueError("Fusion drawing bundle members disagree with design graph")
    Layout = tuple(PackageSlot(Entry.Name, Entry.Layout) for Entry in Package.Entries)
    return DrawingBundle(Model, Drawing, Documents, Layout)
