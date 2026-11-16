from convert.adapters.solidworks.Container.Archive import KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import (
    KConfigClass,
    KNodeNameClass,
    KRootClass,
    KVisualClass,
)
from convert.adapters.solidworks.Container.Definition import KFirstLoadArrayIndex

# the opening reader recognizes only the ordinary pinned discovery profile
KBuildVersion = 2026225
KFileSession = 370108
KNodeOpeningBits = 0x4000000000000000


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
    RequireArch(
        Cursor.ReadInts("<6IB4I"),
        (0, 0, 101, 0, 0, 0, 0, Generation, 0, 0, KBuildVersion),
        "CMgr opening identity",
    )
    Cursor.ReadNull()
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadValue("<BHHB2Ifd")),
        ("", (0, 0xFFFF, 0, 3, 0xFFFFFFFF, 0xFFFFFFFF, -1.0, 0.0)),
        "CMgr opening display settings",
    )
    Cursor.ReadNull()
    Display = Cursor.ReadInts("<3IHI2IH2I")
    RequireArch(
        (Display[:5], Display[7:]),
        ((0, 4, 0, 0, 0xFFFFFFFF), (2, KFileSession, 1)),
        "CMgr opening display state",
    )
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
