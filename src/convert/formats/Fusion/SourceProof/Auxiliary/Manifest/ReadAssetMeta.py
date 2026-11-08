# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ManifestCursor import (
    ManifestCursor,
)

# asset versions are separate from application versions in the root document
KAssetKeys = ("Application", "ParaMesh", "Server", "VolField")

# exact segment declarations keep the three native streams in the same asset
KAssetSegments = (
    SegmentKind.KDesign,
    SegmentKind.KAct,
    SegmentKind.KBrowser,
)


# the active manifest binds the asset identity to the change table snapshot token
def ReadAssetMeta(DataValue: bytes) -> tuple[str, str, tuple[tuple[str, int], ...]]:
    Cursor = ManifestCursor(DataValue)
    if Cursor.ReadText(True) != "FusionAssetName":
        raise ValueError("Unsupported Fusion active manifest format")
    AssetId = Cursor.ReadGuid()
    SnapshotId = Cursor.ReadGuid()
    if Cursor.ReadText() != "FusionAssetType" or Cursor.ReadWord() != 20:
        raise ValueError("Unsupported Fusion active manifest header")
    Versions = Cursor.ReadVersions(KAssetKeys)
    if (
        Cursor.ReadText() != "Neutron3DAssetType"
        or Cursor.ReadWord() != 0
        or Cursor.TakeBytes(1) != b"\x00"
        or Cursor.ReadCount(1) != 1
        or Cursor.ReadText() != "physicalChangeGuid"
    ):
        raise ValueError("Unsupported Fusion active manifest properties")
    Cursor.ReadGuid()
    if Cursor.ReadWord() != 0 or Cursor.ReadWord() not in (5, 7):
        raise ValueError("Unsupported Fusion active manifest segment header")
    if Cursor.ReadCount(len(KAssetSegments)) != len(KAssetSegments):
        raise ValueError("Invalid Fusion active manifest segment count")
    for Index, Segment in enumerate(KAssetSegments):
        if (
            Cursor.ReadWord() != Index
            or Cursor.ReadText() != Segment.value
            or Cursor.ReadText() != Segment.value
        ):
            raise ValueError("Invalid Fusion active manifest segment entry")
    Cursor.CheckEnd()
    return AssetId, SnapshotId, Versions
