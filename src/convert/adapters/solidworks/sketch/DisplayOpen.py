from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.LocalFrame import ReadLocalPose
from convert.adapters.solidworks.sketch.DisplayFields import ReadEmptyTexts, ReadNulls


# the model and sketch variants share their display frame before choosing the mode
def ReadDisplayBase(Cursor: ArchiveCursor, SketchMode: bool) -> None:
    RequireArch(Cursor.ReadInts("<H"), (0,), "witnessed display opening")
    ReadNulls(Cursor, 3)
    Visual = Cursor.ReadValue("<2i2HBIHhf2Hi")
    RequireArch(
        Visual[:-1],
        (0, 0, 65535, 0, 3, 0xFFFFFFFF, 0, 0, -1, 0, 0),
        "guarded display visual properties",
    )
    RequireArch(
        Visual[-1] in (range(10, 16) if SketchMode else (0,)),
        True,
        "witnessed display visual index",
    )
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadValue("<4i3d2i"),
        (0, KConfigGen, 0, 524416, 0, 0, 0, 0, 0),
        "guarded display model fields",
    )
    Cursor.ReadNull()
    RequireArch(Cursor.ReadPoint(3), (0, 0, 0), "empty display reference point")
    RequireArch(ReadLocalPose(Cursor), (None, (0, 0, 0, 1)), "identity display setup")
    RequireArch(
        Cursor.ReadValue("<2iBd2i"),
        (1, 200 if SketchMode else 201, 0, 0, 0, 0),
        "guarded display mode",
    )


# appearance fields must finish before the shared display can allocate its handle
def ReadDisplayOpen(Cursor: ArchiveCursor, SketchMode: bool = False) -> None:
    ReadDisplayBase(Cursor, SketchMode)
    Cursor.ReadNull()
    StyleValue = Cursor.ReadValue("<d2ihf2ihf8ihf5i")
    RequireArch(StyleValue[-5:], (0, 0, 0, 0, 4), "guarded display appearance mode")
    RequireArch(Cursor.ReadPoint(12), (0,) * 12, "empty saved display positions")
    RequireArch(Cursor.ReadInts("<i"), (2,), "guarded display direction count")
    _ = Cursor.ReadPoint(6)
    ReadEmptyTexts(Cursor, 1)
    Position = Cursor.ReadPoint(3)
    if not SketchMode:
        RequireArch(Position, (0, 0, 0), "guarded feature depth placement")
    RequireArch(Cursor.ReadInts("<i"), (18,), "guarded distance display kind")
    Cursor.ReadNull()
    Settings = Cursor.ReadValue("<i4d4i2diH3id2i")
    RequireArch(Settings[11:16], (0, 0, 0, 0, 0), "empty depth display additions")
    RequireArch(Settings[-2:], (0, 1), "guarded depth handle route")
