from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.DocumentCodec.Form.IntegrationRules import KPowerMap
from convert.formats.Fusion.DocumentCodec.Form.PowerMoment import PowerMoment
from convert.formats.Fusion.DocumentCodec.Form.VectorMath import DotProduct


# the mass accum contract needs a shared interpretation so editable control cages retain their document relationships
def MassAccumMut(
    Total: dict[str, float], Point: KJournalVector, Normal: KJournalVector
) -> None:
    Total["area"] += DotProduct(Normal, Normal) ** 0.5
    Total["volume"] += DotProduct(Point, Normal) / 3.0
    for KeyValue, Powers in KPowerMap.items():
        Total[KeyValue] += PowerMoment(Point, Normal, Powers)
