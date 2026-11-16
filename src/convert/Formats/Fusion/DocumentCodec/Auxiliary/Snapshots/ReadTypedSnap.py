from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.Formats.Fusion.BrepCodec.ReadSnapshot import ReadSnapshot
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.ReadPrismSnap import (
    ReadPrismSnap,
)


# the typed snapshot operation needs a distinct decoding boundary so supporting records retain their owning document relationships
def ReadTypedSnap(
    Payload: bytes, Geometry: GeometryState
) -> SnapshotModel | PrismSnapshot | None:
    Cones = tuple(Value for Value in Geometry.Entities if isinstance(Value, ConeNode))
    try:
        if (
            Geometry.Header.RootCount == 4
            and len(Geometry.Entities) == 59
            and len(Cones) == 1
            and Cones[0].SineAngle == 0
        ):
            return ReadSnapshot(Payload)
        if Geometry.Header.RootCount == 4 and len(Geometry.Entities) == 168:
            return None if Cones else ReadPrismSnap(Payload)
    except ValueError:
        return None
    return None
