from typing import cast as CastValue

from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import RootManifest


def EmitDocument(Value: DocumentHeader) -> bytes:
    if (
        not isinstance(CastValue(object, Value), DocumentHeader)
        or type(Value.SoftwareVersion) is not int
        or not 0 <= Value.SoftwareVersion < 1 << 64
    ):
        raise ValueError("Invalid Fusion document header")
    return EmitRootWire(
        RootManifest(
            Value.TypeName,
            Value.TypeDescription,
            (Value.DocumentId, Value.CurrentVersion),
            (Value.SoftwareVersion & 0xFFFFFFFF, Value.SoftwareVersion >> 32),
            Value.Versions,
            Value.AssetId,
            Value.Ancestry,
            Value.Links,
            Value.Lineage,
        )
    )
