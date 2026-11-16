from struct import pack as PackFields

from SketchMemberStyle import COLOR_STATUS_TYPE, Weight, default_visual, standard_width
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# the local corner and the external point share this solved thin member prefix
def WritePointOpen(
    Writer: ArchiveWriter, Subtype: int, Identity: int, RelationCount: int, Status: int
) -> None:
    Writer.raw(PackFields("<H2i", Subtype, 0, Identity))
    Writer.raw(default_visual())
    Writer.raw(PackFields("<iH", RelationCount, 0))
    # the native ordinary constraint-color branch maps status 2 to color 4
    Writer.raw(COLOR_STATUS_TYPE.pack(4, Status, 1))
    Writer.raw(standard_width(Weight.THIN))


# the optional external object comes before the member's absent name and 2D geometry
def WritePointPose(
    Writer: ArchiveWriter,
    Position: tuple[float, float],
    Mask: int,
    PointType: int,
    HandleCount: int,
) -> None:
    Writer.raw(PackFields("<2Hi", 4, 0, 0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<Bd2I", 0, 1.0, 0, 0))
    Writer.raw(PackFields("<H2d2H", Mask, *Position, PointType, HandleCount))


# the ordinary branch has no sharp geometry, jet or additional external references
def WritePointEnd(Writer: ArchiveWriter) -> None:
    Writer.raw(PackFields("<Hi4d2H", 0, -2, 0.0, 0.0, 0.0, 0.0, 0, 0))
