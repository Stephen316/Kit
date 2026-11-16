from dataclasses import dataclass as DataClass

from CmgrExternal import ExternalFile, ReadExtRecord, WriteExtRecord
from HeaderLogs import KHeaderClass
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# The header keeps document creation and self-reference modification times separately.
@DataClass(frozen=True, slots=True)
class HeaderSelf:
    File: ExternalFile
    ModifiedTime: int


# The log section owns the class and object slots preceding the self reference.
def ReadHeaderSelf(Cursor: ArchiveCursor, Generation: int) -> HeaderSelf:
    RequireArch(KHeaderClass in Cursor.Classes.values(), True, "ModelHeader self owner")
    File, ModifiedTime = ReadExtRecord(Cursor, Generation, SelfReference=True)
    return HeaderSelf(File, ModifiedTime)


# Use the same namespace as the revision logs so CString handles follow their slots.
def WriteHeaderSelf(Writer: ArchiveWriter, Generation: int, State: HeaderSelf) -> None:
    RequireArch(KHeaderClass in Writer.classes, True, "ModelHeader self owner")
    WriteExtRecord(
        Writer,
        Generation,
        State.File,
        SelfReference=True,
        ModifiedTime=State.ModifiedTime,
    )
