from dataclasses import dataclass

from ConfigAnnotations import WriteInheritedWidth
from ConfigDetailOpening import PlainCharFormat, WritePlainCharFormat
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedTableFonts:
    Member: PlainCharFormat
    Shared: PlainCharFormat


def WriteTableBase(Writer: ArchiveWriter, Generation: int, Font: PlainCharFormat) -> None:
    Writer.i32(4)  # base standard
    Writer.i32(0)  # leading zero
    Writer.u32(0)  # trailing-zero settings
    Writer.i16(-1)  # no layer
    Writer.i32(0)  # dual dimension position flags
    for _ in range(2):
        WriteInheritedWidth(Writer)
    WritePlainCharFormat(Writer, Generation, Font)


def WriteRevisionDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(0)  # revision symbol shape
    Writer.i32(0)  # revision symbol type
    Writer.i32(1)  # revision change type
    Writer.u32(0)  # subsequent sheet style
    Writer.i32(0)  # visible row count
    Writer.string("")  # revision placeholder


def WriteBomDefaults(Writer: ArchiveWriter) -> None:
    Writer.u32(0)  # zero quantity display settings
    for _ in range(3):  # the parts-only, indented and top-level custom text members
        Writer.string("")


def WriteHoleDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(0)  # table axes
    Writer.i32(0)  # tag alphanumeric style
    Writer.f64(0.008)  # tag offset
    Writer.f64(0.78539816339745)  # tag angle
    Writer.i32(0)  # combine tags
    Writer.i32(0)  # combine sizes
    Writer.i32(2)  # location precision
    Writer.i32(1)  # show centers
    Writer.i32(1)  # show tags
    Writer.i32(1)  # automatic update
    Writer.i32(0)  # reuse deleted tags
    Writer.i32(0)  # add new tags at end
    Writer.i32(2)  # dual location precision
    Writer.i32(0)  # show ansi inch size


def WriteBendDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(2)  # length precision
    Writer.i32(2)  # angle precision
    Writer.i32(0)  # alphanumeric style
    Writer.i32(2)  # bend allowance precision


def WritePunchDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(0)  # table axes
    Writer.i32(0)  # tag alphanumeric style
    Writer.f64(0.008)  # tag offset
    Writer.f64(0.78539816339745)  # tag angle
    Writer.i32(0)  # combine tags
    Writer.i32(0)  # combine punch types
    Writer.i32(2)  # location precision
    Writer.i32(0)  # the constructor clears the member at offset 0x50
    Writer.i32(2)  # dual location precision
    Writer.i32(1)  # show tags


def WriteSavedTables(Writer: ArchiveWriter, Generation: int, Fonts: SavedTableFonts) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved table definitions")
    Record = ArchiveWriter()
    Record.i32(4)  # table definitions base standard

    WriteTableBase(Record, Generation, Fonts.Member)  # general
    WriteTableBase(Record, Generation, Fonts.Member)
    WriteRevisionDefaults(Record)
    WriteTableBase(Record, Generation, Fonts.Member)
    WriteBomDefaults(Record)
    WriteTableBase(Record, Generation, Fonts.Member)
    WriteHoleDefaults(Record)
    WritePlainCharFormat(Record, Generation, Fonts.Shared)

    WriteTableBase(Record, Generation, Fonts.Member)  # title block
    WriteTableBase(Record, Generation, Fonts.Member)  # weld
    Record.i32(0)  # weld bead quantity tag on both sides
    WriteTableBase(Record, Generation, Fonts.Member)
    WriteBendDefaults(Record)
    WriteTableBase(Record, Generation, Fonts.Member)
    WritePunchDefaults(Record)
    WriteTableBase(Record, Generation, Fonts.Member)  # family
    Record.u32(0)  # dimension as family table name

    Record.f64(0.0005)  # horizontal cell padding
    Record.f64(0.001)  # vertical cell padding
    Writer.raw(Record.build())
