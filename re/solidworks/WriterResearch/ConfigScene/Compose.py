from dataclasses import dataclass as Dataclass
from uuid import UUID

from ConfigEnvironment import ConfigEnvironment, WriteConfigEnvironment
from ConfigSavedViews import WriteSavedViews
from ConfigScene.Annotation import WriteAnnotViews
from ConfigScene.ModelLists import PartMarker, WriteModelLists
from ConfigScene.SketchBlock import WriteSketchBlock
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Cmgr import Stamp


# Model scene, annotation placement and the partition mark have different owners.
@Dataclass(frozen=True, slots=True)
class ConfigScene:
    Environment: ConfigEnvironment
    BlockClock: Stamp
    BlockIdentity: UUID
    FirstAnnotation: str
    IncludeTop: bool
    Marker: PartMarker


# The resolved feature list reuses the environment object from this archive map.
@Dataclass(frozen=True, slots=True)
class ConfigSceneSlots:
    Environment: int
    SketchBlock: int


def WriteConfigScene(
    Writer: PartArchiveWriter, Generation: int, State: ConfigScene
) -> ConfigSceneSlots:
    Environment = WriteConfigEnvironment(Writer, Generation, State.Environment)
    WriteSavedViews(Writer, Generation)
    Block = WriteSketchBlock(Writer, Generation, State.BlockClock, State.BlockIdentity)
    WriteAnnotViews(Writer, Generation, State.FirstAnnotation, State.IncludeTop)
    WriteModelLists(Writer, Generation, State.Marker)
    return ConfigSceneSlots(Environment, Block)
