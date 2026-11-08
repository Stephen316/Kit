# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable

from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    KDesignPrefix as KDesignPrefix,
)
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionArchive
from convert.formats.Fusion.RecordSpan import RecordSpan


# standalone design readers retain their compact data and span return contract
def ReadDesignZip(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> tuple[bytes, tuple[RecordSpan, ...]]:
    with OpenFusionArchive(DataValue, InflateZstd) as Session:
        return Session.ReadDesign()
