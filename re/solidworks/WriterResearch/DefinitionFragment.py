from struct import pack as PackFields

from DefinitionOptions import EncodeDefinitionOptions, ReadDefinitionOptions
from DefinitionTail import EncodePartDefinitionTail, ReadPartDefinitionTail
from JournalAttach import JournalAttach
from convert.adapters.solidworks.container.Archive import KNullTag, EncodeNull
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor

# these document constructor values precede the empty dword array
KBeforeDwordArray = (1, 1, 0, 1, 0)

# these constructor values include updated rules and the initial tree order type
KBeforeExcelTable = (1, 1, 0, 0, 0, 2)

# the final values include the base document default for new configuration part numbers
KAfterExcelTable = (0, 0, 0, 3, 1, 0)


# the part tail verifies the exact stream end after the supported document fields
def ReadDefinitionFragment(
    BlobValue: bytes, Offset: int, Generation: int
) -> tuple[JournalAttach, int, float]:
    Attachment, Counter, OptionsEnd = ReadDefinitionOptions(
        BlobValue, Offset, Generation
    )
    Cursor = FieldCursor(BlobValue, OptionsEnd)
    RequireArch(
        Cursor.ReadInts("<5i"), KBeforeDwordArray, "Definition state before DWORD array"
    )
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty Definition DWORD array count")
    RequireArch(
        Cursor.ReadInts("<6i"), KBeforeExcelTable, "Definition state before Excel table"
    )
    RequireArch(
        Cursor.ReadInts("<H"), (KNullTag,), "null Definition Excel table pointer"
    )
    RequireArch(
        Cursor.ReadInts("<6i"), KAfterExcelTable, "Definition state after Excel table"
    )
    TerminalValue = ReadPartDefinitionTail(BlobValue, Cursor.Offset, Generation)
    return Attachment, Counter, TerminalValue


# the proven defaults and explicit typed inputs construct a journal to end fragment
def EncodeDefinitionFragment(
    Generation: int, Attachment: JournalAttach, Counter: int, TerminalValue: float
) -> bytes:
    return b"".join(
        (
            EncodeDefinitionOptions(Generation, Attachment, Counter),
            PackFields("<5iH6i", *KBeforeDwordArray, 0, *KBeforeExcelTable),
            EncodeNull(),
            PackFields("<6i", *KAfterExcelTable),
            EncodePartDefinitionTail(Generation, TerminalValue),
        )
    )
