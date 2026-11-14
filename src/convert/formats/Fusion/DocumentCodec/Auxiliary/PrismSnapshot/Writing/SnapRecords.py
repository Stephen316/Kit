from convert.formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.formats.Fusion.BrepCodec.Topology.OffsetRecord import OffsetRecord
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.RegionRecords import (
    RegionRecords,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.SnapshotAttrs import (
    SnapshotAttrs,
    SnapshotHeads,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.SolidRecords import (
    SolidRecords,
)
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def SnapRecords(Value: PrismSnapshot) -> tuple[GeometryRecord, ...]:
    Solid = SolidRecords(Value.Frame)
    Roots = (
        Solid[0],
        OffsetRecord(Solid[1]),
        MakeRecord("body", (EntityRef(88), EntityRef(-1), EntityRef(-1))),
        MakeRecord("body", (EntityRef(113), EntityRef(-1), EntityRef(-1))),
    )
    Owned = tuple(OffsetRecord(Record) for Record in Solid[2:])
    Topology = (
        *Roots,
        *Owned,
        *RegionRecords(Value.Profile, 88, 2),
        *RegionRecords(Value.Sketch, 113, 3),
    )
    return (*AssignHeads(Topology, SnapshotHeads()), *SnapshotAttrs(Value))
