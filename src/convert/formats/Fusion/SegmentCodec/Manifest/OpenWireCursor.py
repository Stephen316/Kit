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
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KMaxManifestBytes,
)


# standalone payload readers use the same bound as the indexed archive reader
def OpenWireCursor(Payload: bytes) -> ManifestCursor:
    if type(Payload) is not bytes or not 0 < len(Payload) <= KMaxManifestBytes:
        raise ValueError("Invalid Fusion manifest payload size")
    return ManifestCursor(Payload)
