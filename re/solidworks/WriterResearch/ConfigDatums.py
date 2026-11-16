from dataclasses import dataclass
from struct import pack as Pack

from ConfigDetailOpening import UnsetCharFormat
from ConfigFinishNote import WriteAnnotationHelper
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedDatumFonts:
    CenterMark: UnsetCharFormat
    Feature: UnsetCharFormat
    Target: UnsetCharFormat


def WriteSavedDatums(Writer: ArchiveWriter, Generation: int, Fonts: SavedDatumFonts) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved datum definitions")
    Record = ArchiveWriter()

    # the center mark retains document size and the initialized display switches
    Record.raw(Pack("<BdBd6B", 0, 0.0, 1, 0.0, 0, 0, 0, 0, 0, 0))
    WriteAnnotationHelper(Record, Generation, Fonts.CenterMark)
    Record.raw(Pack("<I4Bd", 0, 1, 1, 1, 0, 0.0))

    # the datum feature has two unset text fields and an embedded annotation
    Record.raw(Pack("<3B2i", 0, 0, 0, 0, 0))
    Record.string("")
    Record.string("")
    Record.raw(Pack("<3i", 0, 0, 0))
    WriteAnnotationHelper(Record, Generation, Fonts.Feature)

    # datum target defaults include two 30 mm dimensions and an unset layer
    for _ in range(5):
        Record.string("")
    Record.raw(Pack("<2i2di5Bidi3B", 0, 0, 0.03, 0.03, 0, 0, 1, 0, 0, 1, 0, 0.0, -1, 0, 0, 0))
    Record.raw(Pack("<3d", 0.0, 0.0, 0.0))
    WriteAnnotationHelper(Record, Generation, Fonts.Target)
    Writer.raw(Record.build())
