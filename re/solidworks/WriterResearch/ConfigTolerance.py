from dataclasses import dataclass
from struct import pack as Pack

from ConfigDetailOpening import UnsetCharFormat, WriteUnsetCharFormat
from ConfigFinishNote import WriteAnnotationHelper
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedToleranceFonts:
    Main: UnsetCharFormat
    Annotation: UnsetCharFormat


def WriteEmptyToleranceFrame(Writer: ArchiveWriter) -> None:
    Writer.string("")  # frame text
    for _ in range(2):
        Writer.u8(0)
        Writer.string("")
        Writer.string("")
    for _ in range(6):  # six empty short-form string arrays
        Writer.u16(0)
    Writer.i32(0)
    Writer.i32(0)
    Writer.u16(0)  # no datum records
    Writer.raw(EncodeNull())  # first typed tolerance pointer
    Writer.raw(EncodeNull())  # second typed tolerance pointer
    Writer.i32(0)  # empty indicator list


def WriteSavedTolerance(Writer: ArchiveWriter, Generation: int, Fonts: SavedToleranceFonts) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved tolerance helper")
    Record = ArchiveWriter()
    Record.i32(2)  # the constructor initializes frames at indices 0 and 1
    for _ in range(2):
        WriteEmptyToleranceFrame(Record)

    Record.i32(1)  # initial member +0x30
    Record.i32(2)  # initial member +0x34
    Record.string("")
    Record.raw(Pack("<4BiB", 0, 1, 1, 0, 0, 0))
    Record.string("")
    Record.string("")
    Record.u8(ord(" "))  # blank character in member +0x80
    Record.string("")
    Record.string("")
    Record.u8(0)
    Record.string("")
    Record.raw(Pack("<4B", 0, 1, 0, 0))
    WriteUnsetCharFormat(Record, Generation, Fonts.Main)
    WriteAnnotationHelper(Record, Generation, Fonts.Annotation)
    Record.zeros(6)  # six inactive versioned options
    Writer.raw(Record.build())
