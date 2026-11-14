from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.ReadTypedSnap import (
    ReadTypedSnap,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.SnapshotName import (
    SnapshotName,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap


def ReadSnapPart(Value: ContainerPart) -> DocumentSnap:
    SnapshotName(Value.Name)
    if type(Value.Payload) is not bytes or not 0 < len(Value.Payload) <= KJournalBytes:
        raise ValueError("Invalid or oversized Fusion snapshot part")
    Geometry = ReadGeometry(Value.Payload)
    Typed = ReadTypedSnap(Value.Payload, Geometry)
    return DocumentSnap(Value.Name, Geometry if Typed is None else Typed)
