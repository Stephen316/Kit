from dataclasses import dataclass as Dataclass

from BossResolve import ResolvedBossSlots, ResolvedBossState, WriteResolvedBoss
from ConfigResolvedFraming import FramedArchive
from OrdinaryConfig import OrdinaryConfigArchive
from OrdinaryProfile import OrdinaryProfile, OrdinaryProfileSlots, WriteOrdinaryProfile
from OrdinaryResolved import BeginResolvedPart, ResolvedSystem
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


@Dataclass(frozen=True, slots=True)
class OrdinaryResolvedArchive:
    Framed: FramedArchive
    Profile: OrdinaryProfileSlots
    Boss: ResolvedBossSlots | None


# A single allocation map serves the system features, profile and optional boss.
def BuildOrdinaryResolved(
    Generation: int,
    Config: OrdinaryConfigArchive,
    System: ResolvedSystem,
    Profile: OrdinaryProfile,
    Boss: ResolvedBossState | None,
) -> OrdinaryResolvedArchive:
    Atom = Config.History.Atom
    RequireArch(
        Boss is not None, Atom is not None, "configuration and resolved boss agree"
    )
    Writer, Origin = BeginResolvedPart(Generation, Config, System)
    ProfileSlots = WriteOrdinaryProfile(
        Writer, Generation, Config.History, Origin, Profile
    )
    BossSlots = None
    if Boss is not None and Atom is not None:
        BossSlots = WriteResolvedBoss(
            Writer,
            Generation,
            ProfileSlots.Feature,
            ProfileSlots.File,
            Atom,
            tuple(Line.CreationId for Line in Profile.Lines),
            Boss,
            EntryCount=19,
        )
    return OrdinaryResolvedArchive(
        FramedArchive(Writer.build(), Writer.Snapshot()), ProfileSlots, BossSlots
    )
