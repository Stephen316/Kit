from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire


# the document operation needs a distinct decoding boundary so archive members retain their native ownership and reference relationships
def ReadDocument(Payload: bytes) -> DocumentHeader:
    Value = ReadRootWire(Payload)
    return DocumentHeader(
        Value.OpaqueIds[0],
        Value.OpaqueIds[1],
        Value.OpaqueWords[0] | (Value.OpaqueWords[1] << 32),
        Value.Versions,
        Value.AssetId,
        Value.Title,
        Value.Description,
        Value.Ancestry,
        Value.Links,
        Value.Lineage,
    )
