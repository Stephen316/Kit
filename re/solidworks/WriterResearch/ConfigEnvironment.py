from dataclasses import dataclass as Dataclass
from math import isfinite as IsFinite
from struct import pack as PackFields

from CmgrInherited import (
    ArchiveFeature,
    CheckArcFeature,
    ReadArcFeature,
    WriteArcFeature,
)
from PartArchive import PartArchiveWriter
from ResolvedFolders import CheckFolderMap, KNameClass, WriteFolderName
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    EncodeString,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.NamedNode import ReadNamedNode

KEnvironment = "moEnvFolder_c"
KAmbient = "moAmbientLight_c"
KDirectional = "moDirectionLight_c"
KEnvironmentName = "Lights and Cameras"
KEnvironmentTreeId = 6
KLightNames = ("Ambient", "Directional1", "Directional2", "Directional3")
KLightFlags = 0xC0000000
KWhite = 0x00FFFFFF
KLightState = (KWhite, 0, 1, 0, 1)
KLightOptions = (0, 0, 0, 1.0, 1, 16.0, 0)
KEnvironmentReturn = (1, 0)


# Scene presets supply the coefficients and directional vectors separately from feature identity.
@Dataclass(frozen=True, slots=True)
class SceneLight:
    Feature: ArchiveFeature
    Coefficients: tuple[float, ...]
    Direction: tuple[float, ...] | None


@Dataclass(frozen=True, slots=True)
class ConfigEnvironment:
    Folder: ArchiveFeature
    Lights: tuple[SceneLight, ...]


# The shared light serializer is followed by a vector only on a directional subclass.
def ReadConfigLight(Cursor: ArchiveCursor, Generation: int, Index: int) -> SceneLight:
    Class = KAmbient if Index == 0 else KDirectional
    Kind = KDefinitionKind if Index <= 1 else KClassRefKind
    _ = Cursor.TakePointer((Class,), Kind, CompactOnly=True)
    _ = Cursor.TakePointer((KNameClass,), KClassRefKind, CompactOnly=True)
    RequireArch(
        ReadNamedNode(Cursor, (KLightFlags,)),
        (KLightNames[Index], Index + 12),
        "ordinary environment light identity",
    )
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty light member list")
    Feature = ReadArcFeature(Cursor, Generation)
    RequireArch(Cursor.ReadInts("<i"), (0,), "ordinary light prefix")
    Coefficients = Cursor.ReadPoint(3)
    RequireArch(Cursor.ReadInts("<I4i"), KLightState, "ordinary white light state")
    RequireArch(
        Cursor.ReadText(),
        "Ambient-1" if Index == 0 else "Directional-1",
        "ordinary light subtype label",
    )
    RequireArch(Cursor.ReadValue("<3ididI"), KLightOptions, "ordinary light options")
    Direction = None
    if Index:
        Direction = Cursor.ReadPoint(3)
        RequireArch(Cursor.ReadPoint(1), (0.0,), "ordinary directional light return")
    return SceneLight(Feature, Coefficients, Direction)


# These fields return the environment occurrence later aliased by the resolved stream.
def ReadConfigEnvironment(
    Cursor: ArchiveCursor, Generation: int
) -> tuple[ConfigEnvironment, int]:
    RequireArch(Generation, 19000, "ordinary environment generation")
    _, _, Object = Cursor.TakePointer(
        (KEnvironment,), KDefinitionKind, CompactOnly=True
    )
    _ = Cursor.TakePointer((KNameClass,), KClassRefKind, CompactOnly=True)
    RequireArch(
        ReadNamedNode(Cursor, (0x40000000,)),
        (KEnvironmentName, KEnvironmentTreeId),
        "ordinary environment feature identity",
    )
    RequireArch(
        Cursor.ReadInts("<H"), (len(KLightNames),), "ordinary environment lights"
    )
    Lights = tuple(
        ReadConfigLight(Cursor, Generation, Index) for Index in range(len(KLightNames))
    )
    RequireArch(Cursor.ReadInts("<i"), (0,), "environment child list return")
    Folder = ReadArcFeature(Cursor, Generation)
    RequireArch(Cursor.ReadInts("<2i"), KEnvironmentReturn, "environment folder return")
    return ConfigEnvironment(Folder, Lights), Object


# The caller's light settings must be valid before any child allocation is written.
def CheckConfigLight(Generation: int, Light: SceneLight, Directional: bool) -> None:
    CheckArcFeature(Generation, Light.Feature)
    RequireArch(
        len(Light.Coefficients) == 3
        and all(IsFinite(Value) for Value in Light.Coefficients),
        True,
        "three finite light coefficients",
    )
    Direction = Light.Direction
    RequireArch(
        Direction is not None, Directional, "directional light vector ownership"
    )
    if Direction is not None:
        RequireArch(
            len(Direction) == 3 and all(IsFinite(Value) for Value in Direction),
            True,
            "three finite direction coordinates",
        )


# Each concept name and subclass uses the same part archive allocator as the folder.
def WriteConfigLight(
    Writer: PartArchiveWriter, Generation: int, Index: int, Light: SceneLight
) -> None:
    Writer.begin_object(KAmbient if Index == 0 else KDirectional, 1)
    WriteFolderName(
        Writer, EncodeString(KLightNames[Index]), Index + 12, Flags=KLightFlags
    )
    Writer.raw(PackFields("<Hi", 0, 0))
    WriteArcFeature(Writer, Generation, Light.Feature)
    Writer.raw(PackFields("<i3dI4i", 0, *Light.Coefficients, *KLightState))
    Writer.string("Ambient-1" if Index == 0 else "Directional-1")
    Writer.raw(PackFields("<3ididI", *KLightOptions))
    if Light.Direction is not None:
        Writer.raw(PackFields("<4d", *Light.Direction, 0.0))


# This ordinary folder owns four typed lights and no camera objects.
def WriteConfigEnvironment(
    Writer: PartArchiveWriter, Generation: int, State: ConfigEnvironment
) -> int:
    RequireArch(len(State.Lights), len(KLightNames), "ordinary environment light count")
    CheckFolderMap(Writer, (KEnvironment, KAmbient, KDirectional), 13)
    CheckArcFeature(Generation, State.Folder)
    for Index, Light in enumerate(State.Lights):
        CheckConfigLight(Generation, Light, Index != 0)
    Writer.begin_object(KEnvironment, 1)
    EnvironmentObject = Writer.next_index - 1
    WriteFolderName(Writer, EncodeString(KEnvironmentName), KEnvironmentTreeId)
    Writer.u16(len(State.Lights))
    for Index, Light in enumerate(State.Lights):
        WriteConfigLight(Writer, Generation, Index, Light)
    Writer.i32(0)
    WriteArcFeature(Writer, Generation, State.Folder)
    Writer.raw(PackFields("<2i", *KEnvironmentReturn))
    return EnvironmentObject
