from struct import pack as PackFields
from uuid import UUID

from CmgrInherited import RequireCmgrTime, WriteCmgrFeature
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import Stamp

# the empty manager allocates its own occurrence before its settings refer back to it
KBlockManager = "moSketchBlockMgr_c"


# the ordinary generation uses the documented fresh manager identity and feature clock
def WriteSketchBlock(
    Writer: PartArchiveWriter, Generation: int, Clock: Stamp, Identity: UUID
) -> int:
    RequireCmgrTime(Generation, Clock)
    RequireArch(
        type(Identity) is UUID and Identity.int != 0, True, "fresh sketch block guid"
    )
    RequireArch(
        "moView_c" in Writer.classes
        and "moFeatColorTab_c" in Writer.classes
        and KBlockManager not in Writer.classes,
        True,
        "sketch block follows the standard views and feature color table",
    )
    Writer.BeginObject(KBlockManager, 1)
    Manager = Writer.next_index - 1
    Writer.u16(0)
    Writer.raw(PackFields("<iIii", 0, 0x40000000, -1, 0))
    Writer.string("")
    Writer.i32(0)
    Writer.u16(0)
    Writer.u16(0)
    Writer.i32(0)
    WriteCmgrFeature(Writer, Generation, Clock)
    Writer.raw(Identity.bytes_le)
    Writer.i32(0)
    Writer.ReferenceObject(Manager, KBlockManager)
    Writer.u32(0)
    Writer.u32(0)
    return Manager
