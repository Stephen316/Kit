from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from Display.Compose import KDisplayClass
from Display.EndOwner import KBlindEndClass
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KMarkClass = "moPMarkRecord_c"


# the native partition marker and end specification have separate archive occurrences
@Dataclass(frozen=True, slots=True)
class BossEndSlots:
    MarkObject: int
    EndObject: int


# the active display remains a separate child in the same live map
def WriteBossEndOpen(
    Writer: PartArchiveWriter,
    Generation: int,
    PartitionMarkId: int,
    Reversed: bool,
) -> BossEndSlots:
    RequireArch(Generation, KConfigGen, "ordinary boss end generation")
    RequireArch(type(Reversed), bool, "one explicit blind direction")
    RequireArch(
        type(PartitionMarkId) is int and 0 < PartitionMarkId <= 0x7FFFFFFF,
        True,
        "partition's native mark ID",
    )
    RequireArch(
        Writer.next_index <= KBigObjectTag - 3
        and KBlindEndClass not in Writer.classes
        and all(
            0 < Writer.classes.get(Name, 0) < Writer.next_index
            for Name in (KMarkClass, KDisplayClass)
        ),
        True,
        "existing partition-mark and distance classes before the first end",
    )
    MarkObject = Writer.next_index
    # inactive chooser, action list and spare word precede the present rollback marker
    Writer.raw(PackFields("<H3i", 0, 0, 0, 1))
    Writer.BeginObject(KMarkClass, 1)
    Writer.i32(PartitionMarkId)
    # the ordinary route has empty local maps and null optional body objects
    Writer.raw(PackFields("<13i3Hi", *(0,) * 17))
    Writer.BeginObject(KBlindEndClass, 1)
    EndObject = Writer.next_index - 1
    # null direction reference, one side, no flip, null start and two blind codes
    Writer.raw(PackFields("<H3iH2i", 0, 1, 0, int(Reversed), 0, 0, 0))
    return BossEndSlots(MarkObject, EndObject)
