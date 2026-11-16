from convert.adapters.solidworks.container.Archive import KDefinitionKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.Cmgr import (
    KConfigClass,
    KNodeNameClass,
    KRootClass,
    KVisualClass,
)
from convert.adapters.solidworks.container.Definition import KFirstLoadArrayIndex

# the opening reader recognizes only the ordinary pinned discovery profile
KBuildVersion = 2026225
KFileSession = 370108
KNodeOpeningBits = 0x4000000000000000


# both the manager and the part inherit the same fields after their visual pointer
def ReadCmgrFeature(Cursor: ArchiveCursor, Generation: int) -> None:
    RequireArch(
        Cursor.ReadInts("<iiIBiiiiQi"),
        (0, 0, 101, 0, 0, 0, 0, Generation, 0, KBuildVersion),
        "CMgr inherited feature opening",
    )
    Cursor.ReadNull()
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadValue("<BHHBIHhf")),
        ("", (0, 65535, 0, 3, 0xFFFFFFFF, 65535, -1, -1.0)),
        "CMgr inherited feature display style",
    )
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "CMgr inherited feature members")
    Cursor.ReadNull()
    Fields = Cursor.ReadInts("<IBBiiiIIHii")
    RequireArch(
        (Fields[:6], Fields[8:]),
        ((0, 4, 0, 0, 0, -1), (2, KFileSession, 1)),
        "CMgr inherited feature return",
    )


# the typed pointer walk supplies the visual body and its inherited allocation map
def ReadCmgrOpening(BlobValue: bytes, Generation: int) -> ArchiveCursor:
    RequireArch(Generation, 19000, "CMgr opening generation")
    Cursor = ArchiveCursor(BlobValue, 0, KFirstLoadArrayIndex, {}, {})
    _ = Cursor.TakePointer((KRootClass,), KDefinitionKind, CompactOnly=True)
    Cursor.ReadNull()
    RequireArch(
        (Cursor.ReadInts("<QII"), Cursor.ReadText(), Cursor.ReadInts("<I")),
        ((KNodeOpeningBits, 0xFFFFFFFF, 0), "", (0,)),
        "CMgr root opening",
    )
    Cursor.ReadNull()
    ReadCmgrFeature(Cursor, Generation)
    _ = Cursor.TakePointer((KConfigClass,), KDefinitionKind, CompactOnly=True)
    _ = Cursor.TakePointer((KNodeNameClass,), KDefinitionKind, CompactOnly=True)
    RequireArch(
        (
            Cursor.ReadText(),
            Cursor.ReadInts("<QII"),
            Cursor.ReadText(),
            Cursor.ReadInts("<I"),
        ),
        ("Default", (KNodeOpeningBits, 0, 512), "", (0,)),
        "CMgr named part configuration",
    )
    _ = Cursor.TakePointer((KVisualClass,), KDefinitionKind, CompactOnly=True)
    return Cursor
