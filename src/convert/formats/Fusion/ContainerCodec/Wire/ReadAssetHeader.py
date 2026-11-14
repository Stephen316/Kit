from uuid import UUID as ParseUuid

from convert.formats.Fusion.ContainerCodec.ContainerLayout import KMaxProperties
from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.AssetLink import AssetLink
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.formats.Fusion.ContainerCodec.Wire.EmitAssetHeader import EmitAssetHeader
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetKind,
    KAssetName,
    KAssetRole,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KAssetMarker,
    KMaxLinks,
    KUnchangedGuid,
)
from convert.formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ManifestCursor import (
    ManifestCursor,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
)


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
