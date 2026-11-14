from convert.formats.Fusion.BrepCodec.Topology.RegionCoedge import MakeRegionUse
from convert.formats.Fusion.BrepCodec.Topology.RegionEdge import MakeRegionEdge
from convert.formats.Fusion.BrepCodec.Topology.RegionFace import MakeRegionFace
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildRegion(
    BodyRoot: int, Start: int, IsDouble: bool
) -> tuple[GeometryRecord, ...]:
    return (
        MakeRecord("lump", (EntityRef(-1), EntityRef(Start + 1), EntityRef(BodyRoot))),
        MakeRecord(
            "shell",
            (
                EntityRef(-1),
                EntityRef(-1),
                EntityRef(Start + 2),
                EntityRef(-1),
                EntityRef(Start),
            ),
        ),
        MakeRegionFace(Start, IsDouble),
        MakeRecord("loop", (EntityRef(-1), EntityRef(Start + 4), EntityRef(Start + 2))),
        MakeRegionUse(Start),
        MakeRegionEdge(Start),
        MakeRecord("vertex", (EntityRef(Start + 5), 0, EntityRef(Start + 9))),
    )
