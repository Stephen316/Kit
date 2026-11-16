from struct import pack as PackFields

from JournalAttach import JournalAttach
from MaterialManager import EncodeEmptyMaterialManager, ReadEmptyMaterialManager
from Notebook import EncodeNotebook, ReadNotebook
from convert.adapters.solidworks.Container.Archive import EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor

# the measured fragment admits only the proven part document generation
KDefinitionOptionsGeneration = 19000

# the manager prefix includes the document state empty arrays and presence byte
KMaterialLeadFormat = "<iBB3HB"

# the supported manager prefix uses the measured document state and empty arrays
KMaterialLeadDefaults = (0, 0, 1, 0, 0, 0, 1)

# the two short array counts precede six signed document state words
KDocumentStateFormat = "<2H6i"

# construction leaves both string arrays empty and the six state words zero
KDocumentStateDefaults = (0,) * 8

# the line color is the unsigned word among the signed rendering options
KRenderingOptionsFormat = "<6iI5i"

# the renderer constructor sets bloom threshold radius line thickness and contour defaults
KRenderingOptionsDefaults = (0, 100, 5, 0, 0, 1, 0, 0, 0, 1, 0, 0)


# the supported empty strings use the short unicode framing in the document archive
def ReadEmptyDefinitionString(Cursor: FieldCursor) -> None:
    Start = Cursor.Offset
    TextValue = Cursor.ReadText()
    RequireArch(
        (TextValue, Cursor.Offset - Start), ("", 4), "empty Unicode Definition string"
    )


# this fragment returns the first document field beyond the proven rendering options
def ReadDefinitionOptions(
    BlobValue: bytes, Offset: int, Generation: int
) -> tuple[JournalAttach, int, int]:
    RequireArch(
        Generation, KDefinitionOptionsGeneration, "Definition options generation"
    )
    Attachment, NotebookEnd = ReadNotebook(BlobValue, Offset)
    Cursor = FieldCursor(BlobValue, NotebookEnd)
    RequireArch(
        Cursor.ReadInts(KMaterialLeadFormat),
        KMaterialLeadDefaults,
        "Definition material manager prefix",
    )
    Counter, Cursor.Offset = ReadEmptyMaterialManager(BlobValue, Cursor.Offset)
    ReadEmptyDefinitionString(Cursor)
    for _ in range(2):
        RequireArch(Cursor.ReadInts("<H"), (0,), "empty Definition object list count")
        ReadEmptyDefinitionString(Cursor)
    RequireArch(
        Cursor.ReadInts(KDocumentStateFormat),
        KDocumentStateDefaults,
        "Definition document state",
    )
    RequireArch(
        Cursor.ReadInts(KRenderingOptionsFormat),
        KRenderingOptionsDefaults,
        "Definition rendering defaults",
    )
    RequireArch(Cursor.Offset, NotebookEnd + 115, "Definition options end")
    return Attachment, Counter, Cursor.Offset


# typed inputs and constructor defaults are sufficient for the supported fragment
def EncodeDefinitionOptions(
    Generation: int, Attachment: JournalAttach, Counter: int
) -> bytes:
    RequireArch(
        Generation, KDefinitionOptionsGeneration, "Definition options generation"
    )
    EmptyText = EncodeString("")
    EmptyList = PackFields("<H", 0)
    return b"".join(
        (
            EncodeNotebook(Attachment),
            PackFields(KMaterialLeadFormat, *KMaterialLeadDefaults),
            EncodeEmptyMaterialManager(Counter),
            EmptyText,
            EmptyList,
            EmptyText,
            EmptyList,
            EmptyText,
            PackFields(KDocumentStateFormat, *KDocumentStateDefaults),
            PackFields(KRenderingOptionsFormat, *KRenderingOptionsDefaults),
        )
    )
