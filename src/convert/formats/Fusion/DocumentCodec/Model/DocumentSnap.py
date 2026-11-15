from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)


# document snapshot needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class DocumentSnap:
    Name: str
    Snapshot: SnapshotModel | PrismSnapshot | GeometryState
