from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the region roots contract needs a shared interpretation so supporting records retain their owning document relationships
def RegionRoots(
    Region: RegionFrame, Start: int, BodyRoot: int
) -> tuple[GeometryRecord, ...]:
    FaceFields: tuple[KGeometryValue, ...] = (
        EntityRef(-1),
        EntityRef(Start + 3),
        EntityRef(Start + 1),
        EntityRef(-1),
        EntityRef(Start + 4),
        False,
        BodyRoot == 2,
    )
    if BodyRoot == 2:
        FaceFields += (False,)
    Plane = Region.Plane
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
        MakeRecord("face", FaceFields),
        MakeRecord("loop", (EntityRef(-1), EntityRef(Start + 5), EntityRef(Start + 2))),
        MakeRecord(
            "plane-surface",
            (
                Plane.OriginCm,
                Plane.Normal,
                Plane.Basis,
                Plane.ReverseV,
                False,
                False,
                False,
                False,
            ),
        ),
    )
