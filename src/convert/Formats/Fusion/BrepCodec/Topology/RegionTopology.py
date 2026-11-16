from convert.Formats.Fusion.BrepCodec.Topology.RegionCoedge import MakeRegionUse
from convert.Formats.Fusion.BrepCodec.Topology.RegionEdge import MakeRegionEdge
from convert.Formats.Fusion.BrepCodec.Topology.RegionFace import MakeRegionFace
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the region operation needs a consistent construction rule so topology identity survives native history reconstruction
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
