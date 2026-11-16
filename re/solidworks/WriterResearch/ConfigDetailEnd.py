from dataclasses import dataclass
from struct import pack as Pack

from ConfigDatums import SavedDatumFonts, WriteSavedDatums
from ConfigDetailOpening import PointCharFormat, WritePointCharFormat
from ConfigSwift import WriteSwiftDefaults
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class DetailDescriptions:
    SolidBodies: tuple[str, str, str, str]
    SheetMetal: str
    CutListTemplates: tuple[str, str, str]


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedDetailEnd:
    Datums: SavedDatumFonts
    BorderFont: PointCharFormat
    ZoneFont: PointCharFormat
    Descriptions: DetailDescriptions


def WritePrintDefaults(Writer: ArchiveWriter) -> None:
    for Width in (0.00018, 0.00025, 0.00035, 0.0005, 0.0007, 0.001, 0.0014, 0.002):
        Writer.f32(Width)


def WriteZoneDefaults(Writer: ArchiveWriter) -> None:
    Writer.f64(5000.0)  # hatch density
    Writer.i32(3)  # zone origin
    Writer.i32(1)  # zone letter layout
    Writer.u8(0)  # list number first
    Writer.u8(0)  # continue column sequence
    Writer.i32(1)  # apply dimension rounding
    Writer.i32(0)  # rounding method
    Writer.i32(1)  # member +0x54
    Writer.i32(1)  # match custom properties
    Writer.i32(1)  # sheet number
    Writer.i32(1)  # member +0x80
    Writer.f64(0.0025)  # member +0x88
    Writer.raw(Pack("<3d", 0.0085, 0.0085, 0.0085))  # zone data
    Writer.f64(3.0)  # border width
    Writer.f64(3.0)  # zone divider width
    Writer.raw(Pack("<9i", 0, 0, -1, 0, 0, 1, 1, 1, 0))


def WriteDescriptionDefaults(Writer: ArchiveWriter, State: DetailDescriptions) -> None:
    Writer.raw(Pack("<4i", 0, 0, 0, 1))
    for TextValue in State.SolidBodies:
        Writer.string(TextValue)
    Writer.raw(Pack("<4i", 2, 3, 1, 1))
    Writer.string(State.SheetMetal)
    Writer.raw(Pack("<4i", 0, 1, 1, 0))
    for TextValue in State.CutListTemplates:
        Writer.string(TextValue)
    Writer.raw(Pack("<5i", 1, 0, 0, 0, 0))


def WriteSavedDetailEnd(Writer: ArchiveWriter, Generation: int, State: SavedDetailEnd) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved detail return")
    Descriptions = State.Descriptions
    RequireArch(
        (type(Descriptions.SolidBodies), type(Descriptions.CutListTemplates)),
        (tuple, tuple),
        "immutable native description collections",
    )
    RequireArch(
        (len(Descriptions.SolidBodies), len(Descriptions.CutListTemplates)),
        (4, 3),
        "complete native description collections",
    )
    Texts = (
        *Descriptions.SolidBodies,
        Descriptions.SheetMetal,
        *Descriptions.CutListTemplates,
    )
    RequireArch(
        all(isinstance(TextValue, str) for TextValue in Texts),
        True,
        "native descriptions are strings",
    )
    RequireArch(
        all("\x00" not in TextValue for TextValue in Texts),
        True,
        "complete native cut list and solid body descriptions",
    )
    Record = ArchiveWriter()
    WriteSavedDatums(Record, Generation, State.Datums)
    WriteSwiftDefaults(Record)
    WritePrintDefaults(Record)
    WriteZoneDefaults(Record)
    WritePointCharFormat(Record, Generation, State.BorderFont)
    WritePointCharFormat(Record, Generation, State.ZoneFont)
    WriteDescriptionDefaults(Record, Descriptions)
    Record.u16(0)  # the model's shared parameter array is empty before environment
    Writer.raw(Record.build())
