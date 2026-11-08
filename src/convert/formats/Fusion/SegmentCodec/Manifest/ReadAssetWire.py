# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetKind,
    KAssetName,
    KAssetRole,
    KOpaqueWords,
    KPhysicalKey,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import AssetManifest
from convert.formats.Fusion.SegmentCodec.Manifest.OpenWireCursor import OpenWireCursor
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
    KAssetSegments,
)


# exact active payload decoding keeps the opaque extension and segment value available
def ReadAssetWire(Payload: bytes) -> AssetManifest:
    Cursor = OpenWireCursor(Payload)
    if Cursor.ReadText(True) != KAssetName:
        raise ValueError("Unsupported Fusion active manifest format")
    AssetId, SnapshotId = Cursor.ReadGuid(), Cursor.ReadGuid()
    if (Cursor.ReadText(), Cursor.ReadWord()) != (KAssetRole, KWireVersion):
        raise ValueError("Unsupported Fusion active manifest header")
    Versions = Cursor.ReadVersions(KAssetKeys)
    if (
        Cursor.ReadText() != KAssetKind
        or Cursor.ReadWord() != 0
        or Cursor.TakeBytes(1) != b"\0"
        or Cursor.ReadCount(1) != 1
        or Cursor.ReadText() != KPhysicalKey
    ):
        raise ValueError("Unsupported Fusion active manifest properties")
    PhysicalGuid = Cursor.ReadGuid()
    Reserved, OpaqueWord = Cursor.ReadWord(), Cursor.ReadWord()
    if Reserved != 0 or OpaqueWord not in KOpaqueWords:
        raise ValueError("Unsupported Fusion active manifest segment header")
    if Cursor.ReadCount(len(KAssetSegments)) != len(KAssetSegments):
        raise ValueError("Invalid Fusion active manifest segment count")
    for Index, Segment in enumerate(KAssetSegments):
        if (Cursor.ReadWord(), Cursor.ReadText(), Cursor.ReadText()) != (
            Index,
            Segment.value,
            Segment.value,
        ):
            raise ValueError("Invalid Fusion active manifest segment entry")
    Cursor.CheckEnd()
    return AssetManifest(AssetId, SnapshotId, Versions, PhysicalGuid, OpaqueWord)
