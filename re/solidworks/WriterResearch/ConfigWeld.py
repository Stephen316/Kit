from dataclasses import dataclass
from struct import pack as Pack

from ConfigDetailOpening import UnsetCharFormat, WriteUnsetCharFormat
from ConfigFinishNote import WriteSavedFinish
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class WeldFinishFonts:
    Surface: UnsetCharFormat
    Annotation: UnsetCharFormat


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedWeldFonts:
    Main: UnsetCharFormat
    FirstSide: UnsetCharFormat
    SecondSide: UnsetCharFormat
    FirstFinish: WeldFinishFonts
    SecondFinish: WeldFinishFonts


def WriteSavedWeld(Writer: ArchiveWriter, Generation: int, Fonts: SavedWeldFonts) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved weld helper")
    Record = ArchiveWriter()
    Record.u8(0)  # empty weld symbol type
    for _ in range(2):  # eight strings per side
        for _ in range(8):
            Record.string("")
    Record.string("")  # member +0x90
    Record.zeros(4)  # unset flags +0x98 through +0xa4
    Record.string("")  # member +0xa8
    Record.zeros(2)  # unset flags +0xb0 and +0xb4
    for _ in range(2):
        Record.raw(Pack("<2i3B", 0, 0, 0, 0, 0))
    Record.i32(0)  # member +0xd8
    Record.u8(0)  # member +0xdc
    Record.u8(1)  # member +0xe8, set by the weld helper constructor

    for _ in range(5):  # supplemental text members +0x218 through +0x238
        Record.string("")
    Record.zeros(7)  # unset flags +0x240 through +0x258
    WriteUnsetCharFormat(Record, Generation, Fonts.Main)
    for Side in (Fonts.FirstSide, Fonts.SecondSide):
        Record.u8(1)  # the constructor enables both side font settings
        WriteUnsetCharFormat(Record, Generation, Side)
    for Finish in (Fonts.FirstFinish, Fonts.SecondFinish):
        WriteSavedFinish(Record, Generation, Finish.Surface, Finish.Annotation)
    Writer.raw(Record.build())
