from uuid import UUID as ParseUuid

from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KMaxProperties
from convert.Formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.Formats.Fusion.ContainerCodec.Model.AssetLink import AssetLink
from convert.Formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.Formats.Fusion.ContainerCodec.Wire.EmitAssetHeader import EmitAssetHeader
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetKind,
    KAssetName,
    KAssetRole,
    KWireVersion,
)
from convert.Formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KAssetMarker,
    KMaxLinks,
    KUnchangedGuid,
)
from convert.Formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor
from convert.Formats.Fusion.SourceProof.Auxiliary.Manifest.ManifestCursor import (
    ManifestCursor,
)
from convert.Formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
)


# the link tail operation needs a distinct decoding boundary so archive members retain their native ownership and reference relationships
def ReadLinkTail(Cursor: ManifestCursor) -> str:
    if Cursor.ReadWord() != KAssetMarker:
        raise ValueError("Unsupported Fusion asset link marker")
    Value = Cursor.ReadText(True, Maximum=36)
    if Value == KUnchangedGuid:
        return Value
    try:
        GuidValue = ParseUuid(Value)
    except ValueError as ErrorInfo:
        raise ValueError("Invalid Fusion asset link change GUID") from ErrorInfo
    if str(GuidValue) != Value:
        raise ValueError("Invalid Fusion asset link change GUID")
    return Value


# the asset header operation needs a distinct decoding boundary so archive members retain their native ownership and reference relationships
def ReadAssetHeader(Payload: bytes) -> AssetHeader:
    Cursor = OpenWireCursor(Payload)
    if Cursor.ReadText(True) != KAssetName:
        raise ValueError("Unsupported Fusion asset name")
    AssetId, SnapshotId = Cursor.ReadGuid(), Cursor.ReadGuid()
    if (Cursor.ReadText(), Cursor.ReadWord()) != (KAssetRole, KWireVersion):
        raise ValueError("Unsupported Fusion asset header")
    Versions = Cursor.ReadVersions(KAssetKeys)
    if (Cursor.ReadText(), Cursor.TakeBytes(1)) != (KAssetKind, b"\0"):
        raise ValueError("Unsupported Fusion asset property header")
    SubType = Cursor.ReadText()
    Properties = tuple(
        (Cursor.ReadText(), Cursor.ReadText(True))
        for _ in range(Cursor.ReadCount(KMaxProperties))
    )
    Links = tuple(
        AssetLink(
            Cursor.ReadGuid(),
            Cursor.ReadGuid(),
            Cursor.ReadGuid(),
            Cursor.ReadWord(),
            ReadLinkTail(Cursor),
        )
        for _ in range(Cursor.ReadCount(KMaxLinks))
    )
    NextSegmentId = Cursor.ReadWord()
    Segments = tuple(
        SegmentSlot(
            Cursor.ReadWord(), SegmentKind(Cursor.ReadText()), Cursor.ReadText()
        )
        for _ in range(Cursor.ReadCount(3))
    )
    Cursor.CheckEnd()
    Result = AssetHeader(
        AssetId,
        SnapshotId,
        Versions,
        NextSegmentId,
        Segments,
        Properties,
        Links,
        SubType,
    )
    _ = EmitAssetHeader(Result)
    return Result
