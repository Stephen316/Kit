# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Callable

from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    KDesignPrefix as DesignPrefix,
)
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.RecordSpan import RecordSpan

KDesignPrefix = DesignPrefix


# standalone design readers retain their compact data and span return contract
def ReadDesignZip(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> tuple[bytes, tuple[RecordSpan, ...]]:
    with OpenFusionZip(DataValue, InflateZstd) as Session:
        return Session.ReadDesign()
