from convert.formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.formats.Fusion.DrawingCodec.Manifest.EmitRoot import EmitRoot
from convert.formats.Fusion.DrawingCodec.Manifest.IsModernWire import IsModernWire
from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KMaxManifestRows,
    KMaxPathText,
    KRootFormat,
)
from convert.formats.Fusion.DrawingCodec.Manifest.RootAsset import RootAsset
from convert.formats.Fusion.DrawingCodec.Manifest.RootLink import RootLink
from convert.formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ManifestCursor import (
    ManifestCursor,
)


def ReadRoot(Payload: bytes) -> DrawingRoot:
    Cursor = OpenWireCursor(Payload)
    if Cursor.ReadText() != KRootFormat:
        raise ValueError("Unsupported Fusion drawing root manifest format")
    DocType, Extension = Cursor.ReadText(), Cursor.ReadText(True)
    TypeName, TypeDescription = Cursor.ReadText(True), Cursor.ReadText(True)
    DocumentId, CurrentVersion = Cursor.ReadGuid(), Cursor.ReadGuid()
    Magic, Version = Cursor.ReadWord(), Cursor.ReadWord()
    IsModern = IsModernWire(Magic, Version)
    Software = Cursor.ReadLong() if IsModern else None
    Modules = tuple(
        (Cursor.ReadText(), Cursor.ReadWord())
        for _ in range(Cursor.ReadCount(KMaxManifestRows))
    )
    VersionIds = tuple(
        Cursor.ReadGuid() for _ in range(Cursor.ReadCount(KMaxManifestRows))
    )
    Marker = Cursor.TakeBytes(1)[0]
    if Marker > 1:
        raise ValueError("Unsupported Fusion drawing reference marker")
    References = (
        tuple(
            ReadRootLink(Cursor, IsModern)
            for _ in range(Cursor.ReadCount(KMaxManifestRows))
        )
        if Marker
        else ()
    )
    ActiveAsset = Cursor.ReadGuid()
    Assets = tuple(
        RootAsset(Cursor.ReadText(True), Cursor.ReadWord(), Cursor.TakeBytes(1)[0])
        for _ in range(Cursor.ReadCount(KMaxManifestRows))
    )
    DocumentName = Cursor.ReadText(True)
    SaveLabel = Cursor.ReadText(True) if IsModern else None
    Cursor.CheckEnd()
    Result = DrawingRoot(
        DocType,
        Extension,
        TypeName,
        TypeDescription,
        DocumentId,
        CurrentVersion,
        Magic,
        Version,
        Software,
        Modules,
        VersionIds,
        bool(Marker),
        References,
        ActiveAsset,
        Assets,
        DocumentName,
        SaveLabel,
    )
    if EmitRoot(Result) != Payload:
        raise ValueError("Fusion drawing root manifest is not canonical")
    return Result


def ReadRootLink(Cursor: ManifestCursor, IsModern: bool) -> RootLink:
    RoleValue = Cursor.ReadText(True, Maximum=KMaxPathText)
    Unresolved = None if IsModern else Cursor.ReadText(True, Maximum=KMaxPathText)
    SourcePath = Cursor.ReadText(True, Maximum=KMaxPathText)
    TargetPath = Cursor.ReadText(True, Maximum=KMaxPathText)
    LocalPath = Cursor.ReadText(True, Maximum=KMaxPathText)
    Words = (Cursor.ReadWord(), Cursor.ReadWord(), Cursor.ReadWord(), Cursor.ReadWord())
    Properties = tuple(
        (
            Cursor.ReadText(True, Maximum=KMaxPathText),
            Cursor.ReadText(True, Maximum=KMaxPathText),
        )
        for _ in range(Cursor.ReadCount(KMaxManifestRows))
    )
    return RootLink(
        RoleValue, Unresolved, SourcePath, TargetPath, LocalPath, Words, Properties
    )
