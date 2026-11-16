from struct import pack as PackFields

from SketchMemberStyle import Weight, default_visual, standard_width
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# points and lines use the same lightweight member state before optional external data
def WriteMemberOpen(
    Writer: ArchiveWriter,
    Mode: int,
    Mark: int,
    Identity: int,
    RefCount: int,
    Display: bytes,
    Width: Weight,
) -> None:
    Writer.raw(PackFields("<H2i", Mode, Mark, Identity))
    Writer.raw(default_visual())
    Writer.raw(PackFields("<iH", RefCount, 0))
    Writer.raw(Display)
    Writer.raw(standard_width(Width))


# the ordinary editable member has no alternate geometry, name or scale override
def WriteMemberEnd(Writer: ArchiveWriter, Flags: int) -> None:
    Writer.raw(PackFields("<2Hi", Flags, 0, 0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<Bd2I", 0, 1.0, 0, 0))
