from convert.formats.Fusion.DrawingCodec.Manifest.AssetLink import AssetLink
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingSlot import DrawingSlot
from convert.formats.Fusion.DrawingCodec.Manifest.EmitAsset import EmitAsset
from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KLegacyVersion,
    KMaxManifestRows,
    KMaxPathText,
    KModernVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor


def ReadAsset(Payload: bytes) -> DrawingAsset:
    Cursor = OpenWireCursor(Payload)
    NameValue, AssetId, RevisionId = (
        Cursor.ReadText(True),
        Cursor.ReadGuid(),
        Cursor.ReadGuid(),
    )
    AssetType, Version = Cursor.ReadText(), Cursor.ReadWord()
    if Version not in (KModernVersion, KLegacyVersion):
        raise ValueError("Unsupported Fusion drawing asset manifest version")
    IsModern = Version == KModernVersion
    Modules = tuple(
        (Cursor.ReadText(), Cursor.ReadWord())
        for _ in range(Cursor.ReadCount(KMaxManifestRows))
    )
    KindValue = Cursor.ReadText()
    HeadValue = (
        (Cursor.ReadWord(), Cursor.TakeBytes(1), Cursor.ReadWord())
        if IsModern
        else (0, Cursor.TakeBytes(1), 0)
    )
    if HeadValue != (0, b"\0", 0):
        raise ValueError("Unsupported Fusion drawing asset property header")
    Links = tuple(
        AssetLink(
            Cursor.ReadText(True, Maximum=KMaxPathText),
            Cursor.ReadGuid(),
            Cursor.ReadGuid(),
        )
        for _ in range(Cursor.ReadCount(KMaxManifestRows))
    )
    LinkWord, Allocation = Cursor.ReadWord(), Cursor.ReadWord()
    ChangeGuid = Cursor.ReadGuid() if IsModern else None
    ChangeWord = Cursor.ReadWord() if IsModern else None
    Segments = tuple(
        DrawingSlot(Cursor.ReadWord(), Cursor.ReadText(), Cursor.ReadText())
        for _ in range(Cursor.ReadCount(KMaxManifestRows))
    )
    Cursor.CheckEnd()
    Result = DrawingAsset(
        NameValue,
        AssetId,
        RevisionId,
        AssetType,
        Version,
        Modules,
        KindValue,
        Links,
        LinkWord,
        Allocation,
        ChangeGuid,
        ChangeWord,
        Segments,
    )
    if EmitAsset(Result) != Payload:
        raise ValueError("Fusion drawing asset manifest is not canonical")
    return Result
