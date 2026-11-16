from dataclasses import dataclass as DataClass

from CmgrVisualPrefix import CmgrVisualFields
from ConfigMaterial import KModelDataClass, WriteConfigMaterial
from ConfigModelBody import ConfigModelBody, WriteModelBody
from ConfigModelView import ConfigModelView, WriteModelView
from ConfigSectionHatch import KPartMaterial
from ConfigUnitFields import ConfigUnitState
from ConfigUnits import WriteConfigUnits
from ConfigVisual import WriteConfigVisual
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KDefinitionKind, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


KInitialAtomCounter = 100


def RequireGeneration(Generation: int) -> None:
    RequireArch(
        (type(Generation), Generation), (int, KConfigGen), "ordinary config generation"
    )


def WriteFirstSplitEnd(Writer: ArchiveWriter, Generation: int) -> None:
    RequireGeneration(Generation)
    RequireArch(KPartMaterial in Writer.classes, True, "filed model material")
    RequireArch(KModelDataClass in Writer.classes, False, "new model data definition")
    Writer.BeginObject(KModelDataClass, 1)
    Writer.raw(EncodeNull())  # absent scene
    Writer.i32(0)  # default feature color setting
    Writer.i32(0)  # empty first body appearance collection
    Writer.i32(0)  # empty second body appearance collection
    Writer.i32(0)  # ordinary part without weldment
    Writer.zeros(12)  # three default part settings
    Writer.i32(0)  # empty ordered key-pair map


def ReadFirstSplitEnd(Cursor: ArchiveCursor, Generation: int) -> int:
    RequireGeneration(Generation)
    RequireArch(KPartMaterial in Cursor.Classes.values(), True, "filed model material")
    _, _, ModelObject = Cursor.TakePointer(
        (KModelDataClass,), KDefinitionKind, CompactOnly=True
    )
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i"), (0,), "default feature color setting")
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "empty body appearance collections")
    RequireArch(Cursor.ReadInts("<i"), (0,), "ordinary part without weldment")
    RequireArch(Cursor.ReadInts("<3i"), (0, 0, 0), "default part settings")
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty ordered key-pair map")
    return ModelObject


@DataClass(frozen=True)
class ConfigFirstSplitBody:
    Visual: CmgrVisualFields
    Units: ConfigUnitState
    View: ConfigModelView
    Model: ConfigModelBody
    DensityKgM3: float


# the root constructor already established the name and enclosing part
def WriteFirstSplitBody(
    Writer: ArchiveWriter, Generation: int, State: ConfigFirstSplitBody
) -> None:
    WriteConfigVisual(
        Writer, Generation, State.Visual, RealViewPresent=True, DspbrPresent=True
    )
    WriteConfigUnits(Writer, Generation, State.Units)
    WriteModelView(Writer, Generation, State.View)
    WriteModelBody(Writer, Generation, State.Model)
    WriteConfigMaterial(Writer, Generation, State.DensityKgM3)
    WriteFirstSplitEnd(Writer, Generation)


def OrdinaryAtomIds(AtomCount: int) -> tuple[int, ...]:
    RequireArch(
        type(AtomCount) is int and AtomCount in (0, 1),
        True,
        "standalone sketch or single Boss atom count",
    )
    return tuple(range(KInitialAtomCounter + 1, KInitialAtomCounter + AtomCount + 1))


def WriteSecondSplitStart(
    Writer: ArchiveWriter, Generation: int, AtomCount: int
) -> tuple[int, ...]:
    RequireGeneration(Generation)
    RequireArch(KModelDataClass in Writer.classes, True, "filed model data")
    AtomIds = OrdinaryAtomIds(AtomCount)
    Writer.u16(0)  # the root list is serialized in ResolvedFeatures
    Writer.i32(0)  # enclosing moNodeList trailer
    Writer.i32(KInitialAtomCounter + len(AtomIds))
    Writer.i32(len(AtomIds))
    return AtomIds


def ReadSecondSplitStart(Cursor: ArchiveCursor, Generation: int) -> tuple[int, ...]:
    RequireGeneration(Generation)
    RequireArch(KModelDataClass in Cursor.Classes.values(), True, "filed model data")
    InlineCount, InlineTail, AtomCounter, AtomCount = Cursor.ReadInts("<Hiii")
    RequireArch((InlineCount, InlineTail), (0, 0), "separately filed root feature list")
    AtomIds = OrdinaryAtomIds(AtomCount)
    RequireArch(
        AtomCounter, KInitialAtomCounter + len(AtomIds), "fresh standalone atom counter"
    )
    return AtomIds
