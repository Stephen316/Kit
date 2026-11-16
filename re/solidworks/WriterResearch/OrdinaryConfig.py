from dataclasses import dataclass as Dataclass

from ConfigAtomManager import BossAtomBody
from ConfigDetailComposition import ConfigDetail, WriteConfigDetail
from ConfigHistory import ConfigHistory, WriteConfigHistory
from ConfigMass.CacheList import RectMassCache, WriteMassList
from ConfigResolvedFraming import BeginConfigArchive, FramedArchive, WriteConfigSplit
from ConfigRoot import ConfigRootState, WriteConfigRoot
from ConfigScene.Compose import ConfigScene, ConfigSceneSlots, WriteConfigScene
from ConfigScene.PartEnd import PartEndIds, WriteConfigEnd, WriteMassLead
from ConfigSplitEdges import ConfigFirstSplitBody, WriteFirstSplitBody
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import Stamp


@Dataclass(frozen=True, slots=True)
class ConfigTail:
    Ids: PartEndIds
    Clock: Stamp
    BodyStamp: int | None
    HasStaleCache: bool


@Dataclass(frozen=True, slots=True)
class OrdinaryConfig:
    Root: ConfigRootState
    First: ConfigFirstSplitBody
    Boss: BossAtomBody | None
    Detail: ConfigDetail
    Scene: ConfigScene
    Tail: ConfigTail


@Dataclass(frozen=True, slots=True)
class OrdinaryConfigArchive:
    Framed: FramedArchive
    History: ConfigHistory
    Scene: ConfigSceneSlots


# Physical mass and inertia reuse the first split bounds and material and the live atom.
def CacheForHistory(
    State: OrdinaryConfig, History: ConfigHistory
) -> RectMassCache | None:
    if History.Atom is None:
        return None
    Bounds = State.First.Model.Bounds
    BodyStamp = State.Tail.BodyStamp
    if Bounds is None or BodyStamp is None:
        raise ArchiveError(
            "configuration mass cache needs boss bounds and body update stamp"
        )
    return RectMassCache(
        History.Atom, BodyStamp, Bounds.Minimum, Bounds.Maximum, State.First.DensityKgM3
    )


# The two length fields are resolved after writing their complete populated bodies.
def BuildOrdinaryConfig(
    Generation: int, State: OrdinaryConfig
) -> OrdinaryConfigArchive:
    HasBoss = State.Boss is not None
    RequireArch(
        (
            State.Scene.IncludeTop,
            State.First.Model.Bounds is not None,
            State.Tail.BodyStamp is not None,
        ),
        (HasBoss, HasBoss, HasBoss),
        "ordinary body state shared by configuration owners",
    )
    Writer = BeginConfigArchive()

    def WriteFirst(Active: PartArchiveWriter) -> None:
        WriteConfigRoot(Active, Generation, State.Root)
        WriteFirstSplitBody(Active, Generation, State.First)

    def WriteSecond(
        Active: PartArchiveWriter,
    ) -> tuple[ConfigHistory, ConfigSceneSlots]:
        History = WriteConfigHistory(Active, Generation, State.Boss)
        WriteConfigDetail(Active, Generation, State.Detail)
        Scene = WriteConfigScene(Active, Generation, State.Scene)
        WriteMassLead(Active, Generation)
        WriteMassList(
            Active,
            Generation,
            CacheForHistory(State, History),
            State.Tail.HasStaleCache,
        )
        WriteConfigEnd(Active, Generation, State.Tail.Ids, State.Tail.Clock)
        return History, Scene

    WriteConfigSplit(Writer, WriteFirst)
    History, Scene = WriteConfigSplit(Writer, WriteSecond)
    return OrdinaryConfigArchive(
        FramedArchive(Writer.build(), Writer.Snapshot()), History, Scene
    )
