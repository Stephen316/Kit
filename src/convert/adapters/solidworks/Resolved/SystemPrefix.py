from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.DetailCabinet import (
    DetailCabinet,
    ReadCabinet,
)
from convert.adapters.solidworks.Resolved.FolderNode import FolderNode, ReadFolder
from convert.adapters.solidworks.Resolved.PrincipalDatum import (
    PrincipalDatum,
    ReadPrincipal,
)


# later profile references depend on the allocation of the ordinary document prefix
@Dataclass(frozen=True, slots=True)
class SystemPrefix:
    FirstFolders: tuple[FolderNode, ...]
    Details: DetailCabinet
    LaterFolders: tuple[FolderNode, ...]
    EnvOffset: int
    Environment: int
    Planes: tuple[PrincipalDatum, ...]


# the environment alias must resolve the object that was loaded in the configuration
def ReadSysPrefix(Cursor: ArchiveCursor) -> SystemPrefix:
    FirstFolders = (
        ReadFolder(Cursor, "moCommentsFolder_c", "<2i", (0, 0)),
        ReadFolder(Cursor, "moFavoriteFolder_c", "<4i", (1, 0, 0, 1)),
        ReadFolder(Cursor, "moHistoryFolder_c", "<2iH", (1, 0, 0)),
        ReadFolder(Cursor, "moSelectionSetFolder_c", "<2i6s", (1, 0, b"\0\0\1\0\0\0")),
        ReadFolder(Cursor, "moSensorFolder_c", "<2i", (1, 0)),
        ReadFolder(Cursor, "moDocsFolder_c", "<2i", (1, 0)),
    )
    Details = ReadCabinet(Cursor)
    BodyFolders = (
        ReadFolder(Cursor, "moSurfaceBodyFolder_c", "<4i", (1, 0, 0, 0), 2),
        ReadFolder(Cursor, "moSolidBodyFolder_c", "<4i", (1, 0, 0, 0), 2),
    )
    EnvOffset = Cursor.Offset
    _, _, Environment = Cursor.TakePointer(
        ("moEnvFolder_c",), KObjectRefKind, CompactOnly=True
    )
    LaterFolders = BodyFolders + (
        ReadFolder(Cursor, "moInkMarkupFolder_c", "<2i", (1, 0)),
        ReadFolder(Cursor, "moEqnFolder_c", "<2i", (1, 0)),
        ReadFolder(
            Cursor, "moMaterialFolder_c", "<2i8s", (1, 0, b"\xff\xfe\xff\0\0\0\0\x80")
        ),
    )
    Planes = (
        ReadPrincipal(Cursor, KDefinitionKind),
        ReadPrincipal(Cursor, KClassRefKind),
        ReadPrincipal(Cursor, KClassRefKind),
    )
    RequireArch(
        tuple(
            (Plane.NameValue, Plane.FeatureId, Plane.Geometry.NormalWorld)
            for Plane in Planes
        ),
        (
            ("Front Plane", 2, (0, 0, 1)),
            ("Top Plane", 3, (0, 1, 0)),
            ("Right Plane", 4, (1, 0, 0)),
        ),
        "guarded principal plane identities and orientation",
    )
    return SystemPrefix(
        FirstFolders, Details, LaterFolders, EnvOffset, Environment, Planes
    )
