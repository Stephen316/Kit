from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import RequireCmgrTime, WriteCmgrFeature
from CmgrOpening import CmgrNodeState, WriteCmgrNode
from ConfigScene.ModelLists import KThreadClass
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import Stamp

KExplManager = "moPrtExplViewManager_c"


@Dataclass(frozen=True, slots=True)
class PartEndIds:
    ExplView: int
    Presentation: int
    Configuration: int


# empty text pairs complete the model before four part fields introduce the cache list
def WriteMassLead(Writer: PartArchiveWriter, Generation: int) -> None:
    RequireArch(Generation, 19000, "ordinary part tail generation")
    RequireArch(KThreadClass in Writer.classes, True, "after the model thread manager")
    Writer.i32(0)  # model text-pair count
    Writer.raw(PackFields("<iB2i", 0, 0, 0, 1))


# the manager shares the native feature base and leaves both optional pointers empty
def WriteExplView(
    Writer: PartArchiveWriter, Generation: int, NodeId: int, Clock: Stamp
) -> None:
    Writer.begin_object(KExplManager, 1)
    Writer.raw(EncodeNull())  # absent node name
    WriteCmgrNode(Writer, NodeId, CmgrNodeState(0, 0))
    Writer.raw(EncodeNull())  # absent scene child
    Writer.u16(0)
    Writer.i32(0)
    WriteCmgrFeature(Writer, Generation, Clock)
    Writer.raw(EncodeNull() + EncodeNull())
    Writer.raw(PackFields("<d2iH", 0.0, -1, -1, 0))


# the two tree IDs come from the model header while configuration supplies its own ID
def WriteConfigEnd(
    Writer: PartArchiveWriter, Generation: int, Ids: PartEndIds, Clock: Stamp
) -> None:
    RequireCmgrTime(Generation, Clock)
    RequireArch(
        all(
            type(Value) is int and 0 < Value < 2**31
            for Value in (Ids.ExplView, Ids.Presentation, Ids.Configuration)
        ),
        True,
        "positive exploded view, presentation and configuration identities",
    )
    RequireArch(Ids.Presentation, Ids.ExplView + 1, "consecutive ordinary tree IDs")
    RequireArch(
        KThreadClass in Writer.classes and KExplManager not in Writer.classes,
        True,
        "new exploded view after the model thread manager",
    )
    Writer.i32(0)  # part +0x1400 closes the mass-cache list
    WriteExplView(Writer, Generation, Ids.ExplView, Clock)
    Writer.i32(Ids.Presentation)
    Writer.i32(Ids.Configuration)
    Writer.i32(0)  # supplemental link data absent
    Writer.i32(0)  # empty sheet-metal extension array
    Writer.i32(0)  # empty bounding-box data table
    Writer.i32(0)  # absent part defeature map
    Writer.u32(101)  # initial part +0x18c8 word
    Writer.i32(0)  # absent assembly defeature map
    Writer.i32(0)  # absent part body selection table
