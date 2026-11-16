from collections.abc import Callable

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import (
    KDesignPrefix as DesignPrefix,
)
from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.RecordSpan import RecordSpan

# design prefix must share the design prefix contract so native document reconstruction cannot drift between equivalent names
KDesignPrefix = DesignPrefix


# standalone design readers retain their compact data and span return contract
def ReadDesignZip(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> tuple[bytes, tuple[RecordSpan, ...]]:
    with OpenFusionZip(DataValue, InflateZstd) as Session:
        return Session.ReadDesign()
