from pathlib import PurePosixPath

from CmgrOpening import ReadCmgrOpening
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor


# the post-material color record is preceded by the inline RealView appearance
def ReadRealView(Cursor: FieldCursor) -> None:
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadText(), Cursor.ReadValue("<6di")),
        ("", "Steel", (1.0, 1.0, 0.5, 0.3125, 0.0, 0.0, 0)),
        "CMgr ordinary material prefix",
    )
    RequireArch(
        (Cursor.ReadInts("<5i"), Cursor.ReadText(), Cursor.ReadInts("<2i")),
        ((1, 0, 1, 1, 1), "", (1, 1)),
        "CMgr RealView appearance presence",
    )
    _ = Cursor.ReadInts("<II")
    RequireArch(Cursor.ReadText(), "defaultplastic", "CMgr RealView shader")
    _ = Cursor.ReadValue("<BI10f")
    (Mode,) = Cursor.ReadInts("<i")
    RequireArch(Mode, 1, "CMgr RealView color mode")
    _ = Cursor.ReadValue("<5fi2f")
    MaterialPath = PurePosixPath(Cursor.ReadText().replace("\\", "/"))
    RequireArch(MaterialPath.name.casefold(), "color.p2m", "CMgr RealView color file")
    _ = Cursor.ReadValue("<I2f")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<3fifi13f")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<f")


# the stored colors belong to the enclosing visual object and the body has its own end
def ReadColorSpan(BlobValue: bytes, Generation: int) -> tuple[int, int, int]:
    Cursor = ReadCmgrOpening(BlobValue, Generation)
    ColorValue, _, _ = Cursor.ReadInts("<3I")
    ReadRealView(Cursor)
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadInts("<2i")),
        ("", (0, 0)),
        "CMgr empty material suffix",
    )
    RequireArch(
        (
            Cursor.ReadText(),
            Cursor.ReadInts("<2i"),
            Cursor.ReadText(),
            Cursor.ReadInts("<6i"),
        ),
        ("", (0, 1), "", (0, 1, -1, 0, 0, 1)),
        "CMgr DSPBR appearance presence",
    )
    Start = Cursor.Offset
    _ = Cursor.ReadValue("<26fi18fi2f")
    Paths = tuple(Cursor.ReadText() for _ in range(4))
    RequireArch((Paths, Cursor.ReadText()), (("",) * 4, "basic"), "CMgr DSPBR subtype")
    _ = Cursor.ReadValue("<f")
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadText()),
        ("2025x", ""),
        "CMgr DSPBR library version",
    )
    _ = Cursor.ReadValue("<i6f")
    Paths = tuple(Cursor.ReadText() for _ in range(2))
    _ = Cursor.ReadValue("<2f")
    Paths += tuple(Cursor.ReadText() for _ in range(3))
    RequireArch(Paths, ("",) * 5, "CMgr DSPBR texture paths")
    return ColorValue, Start, Cursor.Offset
