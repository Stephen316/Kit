from convert.formats.Fusion.AssetCodec.ConfigLayout import KConfigPrefix
from convert.formats.Fusion.AssetCodec.SegmentFrame import SegmentFrame
from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KActiveManifest,
    KRootManifest,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import KActivePrefix

# the empty root properties layout is one zero length json field
KPropertiesName = "Properties.dat"


# fixed member paths keep segment data and manifest slots in the same active asset
def MakeAssetRows(
    RootData: bytes,
    AssetData: bytes,
    Frames: tuple[SegmentFrame, ...],
    ConfigFiles: tuple[str, ...],
) -> tuple[ZipAssetRow, ...]:
    Prefixes = tuple(f"{KActivePrefix}{Frame.Segment.value}1/" for Frame in Frames)
    Directories = (KActivePrefix, *Prefixes, *((KConfigPrefix,) if ConfigFiles else ()))
    MemberRows = [ZipAssetRow(NameValue, b"", False) for NameValue in Directories]
    MemberRows.extend(
        (
            ZipAssetRow(KRootManifest, RootData, True),
            ZipAssetRow(KPropertiesName, bytes(4), False),
            ZipAssetRow(KActiveManifest, AssetData, True),
        )
    )
    for Prefix, Frame in zip(Prefixes, Frames, strict=True):
        MemberRows.append(ZipAssetRow(Prefix + "BulkStream.dat", Frame.BulkData, True))
        MemberRows.append(ZipAssetRow(Prefix + "MetaStream.dat", Frame.MetaData, True))
    MemberRows.extend(ZipAssetRow(NameValue, b"{}", False) for NameValue in ConfigFiles)
    return tuple(MemberRows)
