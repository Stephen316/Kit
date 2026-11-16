from dataclasses import dataclass as Dataclass, replace as Replace

from ConfigResolvedFraming import BeginResolvedArchive
from OrdinaryConfig import OrdinaryConfigArchive
from PartArchive import PartArchiveState, PartArchiveWriter
from ResolvedCabinet import CabinetState, ReadCabinetRec, WriteCabinetRec
from ResolvedFolderTail import LateFolders, ReadLateFolders, WriteLateFolders
from ResolvedFolders import ReadSysFolders, SystemFolder, WriteSysFolders
from ResolvedOrigin import OriginSlots, OriginState, ReadOriginRec, WriteOriginRec
from ResolvedPrincipal import PrincipalPlane, ReadResolvedPlanes, WriteResolvedPlanes
from convert.adapters.solidworks.Config.RootLayout import KRootClass
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# These are the default roots before the authored profile and optional boss.
@Dataclass(frozen=True, slots=True)
class ResolvedSystem:
    Folders: tuple[SystemFolder, ...]
    Cabinet: CabinetState
    LateFolders: LateFolders
    Planes: tuple[PrincipalPlane, ...]
    Origin: OriginState


# System owners share the same cursor until the first authored feature.
def ReadResolvedSystem(Cursor: ArchiveCursor, Generation: int) -> ResolvedSystem:
    return ResolvedSystem(
        ReadSysFolders(Cursor, Generation),
        ReadCabinetRec(Cursor, Generation),
        ReadLateFolders(Cursor, Generation),
        ReadResolvedPlanes(Cursor, Generation),
        ReadOriginRec(Cursor, Generation),
    )


# The atom allocation records whether the resolved root list also owns a boss.
def BeginOrdinaryResolved(
    Generation: int, ConfigState: PartArchiveState, System: ResolvedSystem
) -> tuple[PartArchiveWriter, OriginSlots]:
    AtomCount = sum(Name == "moAtom_c" for _, Name in ConfigState.Objects)
    RequireArch(AtomCount in (0, 1), True, "ordinary resolved feature history")
    # The cabinet, environment alias and Origin each contribute one root.
    SystemCount = (
        len(System.Folders) + len(System.LateFolders.Folders) + len(System.Planes) + 3
    )
    RootCount = SystemCount + 1 + AtomCount
    Writer = BeginResolvedArchive(Generation, ConfigState, RootCount)
    WriteSysFolders(Writer, Generation, System.Folders)
    WriteCabinetRec(Writer, Generation, System.Cabinet)
    WriteLateFolders(Writer, Generation, System.LateFolders)
    WriteResolvedPlanes(Writer, Generation, System.Planes)
    return Writer, WriteOriginRec(Writer, Generation, System.Origin)


# Cross-stream pointers come from the generated configuration's actual allocation.
def BeginResolvedPart(
    Generation: int, Config: OrdinaryConfigArchive, System: ResolvedSystem
) -> tuple[PartArchiveWriter, OriginSlots]:
    State = Config.Framed.State
    (Part,) = (Index for Index, Name in State.Objects if Name == KRootClass)
    Bound = Replace(
        System,
        Origin=Replace(System.Origin, PartObject=Part),
        LateFolders=Replace(System.LateFolders, Environment=Config.Scene.Environment),
    )
    return BeginOrdinaryResolved(Generation, State, Bound)
