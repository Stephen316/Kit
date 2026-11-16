from convert.Formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.ReadTypedSnap import (
    ReadTypedSnap,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.SnapshotName import (
    SnapshotName,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap


# the snapshot part operation needs a distinct decoding boundary so supporting records retain their owning document relationships
def ReadSnapPart(Value: ContainerPart) -> DocumentSnap:
    SnapshotName(Value.Name)
    if type(Value.Payload) is not bytes or not 0 < len(Value.Payload) <= KJournalBytes:
        raise ValueError("Invalid or oversized Fusion snapshot part")
    Geometry = ReadGeometry(Value.Payload)
    Typed = ReadTypedSnap(Value.Payload, Geometry)
    return DocumentSnap(Value.Name, Geometry if Typed is None else Typed)
