from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the roots operation needs a consistent construction rule so geometric values retain their native record boundaries
def BuildRoots() -> tuple[GeometryRecord, ...]:
    return (
        GeometryRecord("asmheader", (EntityRef(-1), -1, CountedText("232.5.0.65535"))),
        MakeRecord("body", (EntityRef(2), EntityRef(-1), EntityRef(-1))),
        MakeRecord("lump", (EntityRef(-1), EntityRef(3), EntityRef(1))),
        MakeRecord(
            "shell",
            (EntityRef(-1), EntityRef(-1), EntityRef(4), EntityRef(-1), EntityRef(2)),
        ),
    )
