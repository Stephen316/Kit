from collections.abc import Sequence
from dataclasses import dataclass as Dataclass

from BossChoice import BossChoiceState, WriteBossChoice
from BossEndOpen import BossEndSlots, WriteBossEndOpen
from BossOpen import BossOpening, WriteBossOpen
from ConfigAtomManager import ConfigAtomBinding
from Display.Compose import BossDisplay, DisplayDraft, WriteDisplayMut
from Display.EndOwner import EncodeBossReturn, EncodeFreshProps, WriteEndStart
from PartArchive import PartArchiveWriter
from Resolved.EndMap import EncodeResolvedEnd
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# display geometry controls the same signed operation that the boss end stores
@Dataclass(frozen=True, slots=True)
class ResolvedBossState:
    Opening: BossOpening
    Choice: BossChoiceState
    PartitionMarkId: int
    Display: BossDisplay
    Draft: DisplayDraft


# the same map retains these owners through the completed feature and list
@Dataclass(frozen=True, slots=True)
class ResolvedBossSlots:
    FeatureObject: int
    End: BossEndSlots
    DisplayObject: int
    StartObject: int


# the first boss follows the generated profile and closes the ordinary resolved list
def WriteResolvedBoss(
    Writer: PartArchiveWriter,
    Generation: int,
    Profile: int,
    File: int,
    Atom: ConfigAtomBinding,
    EdgeIds: Sequence[int],
    State: ResolvedBossState,
    *,
    EntryCount: int,
) -> ResolvedBossSlots:
    RequireArch(EntryCount, 19, "ordinary resolved sketch and one boss")
    Footer = EncodeResolvedEnd(Generation=Generation, EntryCount=EntryCount)
    Properties = EncodeFreshProps(Generation=Generation)
    Owner = WriteBossOpen(Writer, Generation, Profile, File, Atom, State.Opening)
    WriteBossChoice(Writer, Generation, Owner, EdgeIds, State.Choice)
    End = WriteBossEndOpen(
        Writer, Generation, State.PartitionMarkId, State.Display.Geometry.Reverse
    )
    Display = WriteDisplayMut(
        Writer, State.Display, State.Draft, Generation=Generation, ConditionOne=False
    )
    Start = WriteEndStart(Writer, Generation=Generation)
    Writer.raw(Properties)
    Writer.raw(EncodeBossReturn(Generation=Generation))
    Writer.raw(Footer)
    return ResolvedBossSlots(Owner["object_index"], End, Display, Start)
