from dataclasses import dataclass
from struct import pack as Pack

from ConfigDetailOpening import UnsetCharFormat, WriteUnsetCharFormat
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedHelperFonts:
    Finish: UnsetCharFormat
    FinishAnnotation: UnsetCharFormat
    Note: UnsetCharFormat
    NoteAnnotation: UnsetCharFormat


# the initialized annotation helper files two separate leader groups
def WriteAnnotationHelper(Writer: ArchiveWriter, Generation: int, Font: UnsetCharFormat) -> None:
    Writer.raw(Pack("<4iB", 3, -1, 0, 0, 1))
    WriteUnsetCharFormat(Writer, Generation, Font)
    for _ in range(2):
        Writer.raw(Pack("<Bidi", 1, 0, 0.0, 0))


def WriteSavedFinish(
    Writer: ArchiveWriter,
    Generation: int,
    FinishFont: UnsetCharFormat,
    AnnotationFont: UnsetCharFormat,
) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved surface finish helper")
    Record = ArchiveWriter()
    Record.i32(0)  # surface finish type
    for _ in range(10):  # legacy text members at +0x10 through +0x58
        Record.string("")
    Record.raw(Pack("<4Bi4BdB", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 1))
    WriteUnsetCharFormat(Record, Generation, FinishFont)
    Record.u8(0)  # option at +0x120
    Record.u8(0)  # option at +0x124
    WriteAnnotationHelper(Record, Generation, AnnotationFont)
    Record.i32(0)  # angle option
    Record.f64(0.78539816339745)
    Record.string("")  # supplemental texts at +0x88 and +0x90
    Record.string("")
    Record.i32(0)
    Record.i32(0)
    Writer.raw(Record.build())


def WriteSavedNote(
    Writer: ArchiveWriter,
    Generation: int,
    NoteFont: UnsetCharFormat,
    AnnotationFont: UnsetCharFormat,
) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved note helper")
    Record = ArchiveWriter()
    for _ in range(4):  # note text and separately owned legacy text members
        Record.string("")
    Record.raw(Pack("<6BidB", 1, 1, 0, 0, 0, 0, 0, 0.0, 1))
    Record.raw(Pack("<8i2d", 0, 2, 0, 0, 0, 3, 10, 0, 1e-6, 1e-6))
    Record.raw(Pack("<12B", 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1))
    WriteUnsetCharFormat(Record, Generation, NoteFont)
    Record.i32(0)  # late note settings +0x240 and +0x244
    Record.i32(0)
    Record.raw(Pack("<Q", 0))  # empty note helper map
    Record.zeros(3)  # flags +0x138, +0x13c and +0x140
    WriteAnnotationHelper(Record, Generation, AnnotationFont)
    Record.raw(Pack("<2Bid2i", 0, 0, 0, 0.01016, 0, 1))
    Record.string("X")  # quantity delimiter
    Record.raw(Pack("<4i2di2B", 1, 1, 0, 0, 0.0, 0.001, 1, 0, 0))
    Writer.raw(Record.build())


def WriteSavedFinishNote(Writer: ArchiveWriter, Generation: int, Fonts: SavedHelperFonts) -> None:
    Record = ArchiveWriter()
    WriteSavedFinish(Record, Generation, Fonts.Finish, Fonts.FinishAnnotation)
    WriteSavedNote(Record, Generation, Fonts.Note, Fonts.NoteAnnotation)
    Writer.raw(Record.build())
