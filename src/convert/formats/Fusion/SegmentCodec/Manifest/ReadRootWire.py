from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetName,
    KExportLabel,
    KRootFormat,
    KRootMagic,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import RootManifest
from convert.formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor
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
    if (Cursor.ReadWord(), Cursor.TakeBytes(1)) != (0, b"\0"):
        raise ValueError("Unsupported Fusion root manifest asset header")
    AssetId = Cursor.ReadGuid()
    if (
        Cursor.ReadCount(1) != 1
        or Cursor.ReadText(True) != KAssetName
        or Cursor.ReadWord() != 0
        or Cursor.TakeBytes(1) != b"\1"
        or Cursor.ReadText(True) != KExportLabel
    ):
        raise ValueError("Unsupported Fusion root manifest asset entry")
    Cursor.CheckEnd()
    return RootManifest(Title, Description, OpaqueIds, OpaqueWords, Versions, AssetId)
