from collections.abc import Callable
from typing import cast as CastValue

from convert.formats.Fusion.BundleCodec.Json.EmitJson import EmitJson
from convert.formats.Fusion.BundleCodec.Json.EmitModel import EmitModel
from convert.formats.Fusion.DrawingCodec.Bundle.CheckBundle import (
    CheckBundle,
    DrawingObject,
)
from convert.formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import (
    KDescriptionName,
    KManifestName,
)
from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing
from convert.formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage
from convert.formats.Fusion.DrawingCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry


def EmitDrawBundle(
    Value: DrawingBundle, CompressZstd: Callable[[bytes], bytes] | None = None
) -> bytes:
    if not isinstance(CastValue(object, Value), DrawingBundle):
        raise ValueError("Expected a typed Fusion drawing bundle")
    RootValue = DrawingObject(Value.Description)
    CheckBundle(Value.Description, Value.Drawing)
    Others = {
        Entry.MemberPath
        for Entry in Value.Description.Graph.Objects
        if Entry.ObjectId != RootValue.ObjectId
    }
    if {Entry.FileName for Entry in Value.Documents} != Others or len(
        Value.Documents
    ) != len(Others):
        raise ValueError("Fusion drawing bundle payloads disagree with design graph")
    Payloads = {Entry.FileName: Entry.DataValue for Entry in Value.Documents}
    Payloads[KManifestName] = EmitJson({"root": Value.Description.RootPath})
    Payloads[KDescriptionName] = EmitJson(EmitModel(Value.Description))
    Payloads[RootValue.MemberPath] = EmitDrawing(Value.Drawing, CompressZstd)
    Entries = tuple(
        PackageEntry(SlotValue.Name, Payloads.pop(SlotValue.Name), SlotValue.Layout)
        for SlotValue in Value.Layout
        if SlotValue.Name in Payloads
    )
    if Payloads or len(Entries) != len(Value.Layout):
        raise ValueError("Fusion drawing bundle layout disagrees with its members")
    return EmitPackage(DrawingPackage(Entries), CompressZstd)
