# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ManifestCursor import (
    ManifestCursor,
)

# the document header stores these version keys before the selected asset reference
KRootKeys = (
    "Application",
    "CAM",
    "ParaMesh",
    "SimCommon",
    "SimFEACSObjects",
    "SimFluidDynamics",
    "SimStructuralAttributes",
)


# the root manifest locates the active asset without relying on incidental token matches
def ReadRootMeta(DataValue: bytes) -> tuple[str, tuple[tuple[str, int], ...]]:
    Cursor = ManifestCursor(DataValue)
    if (
        Cursor.ReadText() != "3-2-0-0"
        or Cursor.ReadText() != "FusionDocType"
        or Cursor.ReadText(True) != ".f3d"
    ):
        raise ValueError("Unsupported Fusion root manifest format")
    Cursor.ReadText(True)
    Cursor.ReadText(True, AllowControls=True)
    Cursor.ReadGuid()
    Cursor.ReadGuid()
    if Cursor.ReadWord() != 1234 or Cursor.ReadWord() != 20:
        raise ValueError("Unsupported Fusion root manifest header")
    Cursor.ReadLong()
    Versions = Cursor.ReadVersions(KRootKeys)
    if Cursor.ReadWord() != 0 or Cursor.TakeBytes(1) != b"\x00":
        raise ValueError("Unsupported Fusion root manifest asset header")
    AssetId = Cursor.ReadGuid()
    if (
        Cursor.ReadCount(1) != 1
        or Cursor.ReadText(True) != "FusionAssetName"
        or Cursor.ReadWord() != 0
        or Cursor.TakeBytes(1) != b"\x01"
        or Cursor.ReadText(True) != "NA_EXPORT"
    ):
        raise ValueError("Unsupported Fusion root manifest asset entry")
    Cursor.CheckEnd()
    return AssetId, Versions
