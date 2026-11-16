from struct import pack as PackFields

from SketchMember import WriteMemberEnd, WriteMemberOpen
from SketchMemberStyle import COLOR_STATUS_TYPE, Weight
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# the local corner and the external point share this solved thin member prefix
def WritePointOpen(
    Writer: ArchiveWriter, Subtype: int, Identity: int, RelationCount: int, Status: int
) -> None:
    # the native ordinary constraint-color branch maps status 2 to color 4
    WriteMemberOpen(
        Writer,
        Subtype,
        0,
        Identity,
        RelationCount,
        COLOR_STATUS_TYPE.pack(4, Status, 1),
        Weight.THIN,
    )


# the optional external object comes before the member's absent name and 2D geometry
def WritePointPose(
    Writer: ArchiveWriter,
    Position: tuple[float, float],
    Mask: int,
    PointType: int,
    HandleCount: int,
) -> None:
    WriteMemberEnd(Writer, 4)
    Writer.raw(PackFields("<H2d2H", Mask, *Position, PointType, HandleCount))


# the ordinary branch has no sharp geometry, jet or additional external references
def WritePointEnd(Writer: ArchiveWriter) -> None:
    Writer.raw(PackFields("<Hi4d2H", 0, -2, 0.0, 0.0, 0.0, 0.0, 0, 0))
