from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetName,
    KExportLabel,
    KRootFormat,
    KRootMagic,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import KMaxAncestry
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import RootManifest
from convert.formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootLinks import ReadRootLinks
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadRootMeta import KRootKeys


# the complete root payload keeps authorable fields that the source proof does not need
def ReadRootWire(Payload: bytes) -> RootManifest:
    Cursor = OpenWireCursor(Payload)
    if (Cursor.ReadText(), Cursor.ReadText(), Cursor.ReadText(True)) != KRootFormat:
        raise ValueError("Unsupported Fusion root manifest format")
    Title = Cursor.ReadText(True)
    Description = Cursor.ReadText(True, AllowControls=True)
    OpaqueIds = Cursor.ReadGuid(), Cursor.ReadGuid()
    if (Cursor.ReadWord(), Cursor.ReadWord()) != (KRootMagic, KWireVersion):
        raise ValueError("Unsupported Fusion root manifest header")
    OpaqueWords = Cursor.ReadWord(), Cursor.ReadWord()
    Versions = Cursor.ReadVersions(KRootKeys)
    Ancestry = tuple(Cursor.ReadGuid() for _ in range(Cursor.ReadCount(KMaxAncestry)))
    Links = ReadRootLinks(Cursor)
    AssetId = Cursor.ReadGuid()
    if (
        Cursor.ReadCount(1) != 1
        or Cursor.ReadText(True) != KAssetName
        or Cursor.ReadWord() != 0
    ):
        raise ValueError("Unsupported Fusion root manifest asset entry")
    Lineage: tuple[str, str] | None = None
    TailFlag = Cursor.TakeBytes(1)
    if TailFlag == b"\1":
        if Cursor.ReadText(True) != KExportLabel:
            raise ValueError("Unsupported Fusion root manifest export label")
    elif TailFlag == b"\0":
        Lineage = Cursor.ReadText(True), Cursor.ReadText(True)
    else:
        raise ValueError("Unsupported Fusion root manifest terminal flag")
    Cursor.CheckEnd()
    Result = RootManifest(
        Title,
        Description,
        OpaqueIds,
        OpaqueWords,
        Versions,
        AssetId,
        Ancestry,
        Links,
        Lineage,
    )
    _ = EmitRootWire(Result)
    return Result
