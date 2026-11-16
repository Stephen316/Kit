from dataclasses import dataclass

from ConfigDetailOpening import PlainCharFormat, WritePlainCharFormat
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedAnnotationFonts:
    Standard: PlainCharFormat
    WeldRoot: PlainCharFormat
    RevisionCloud: PlainCharFormat


# native annotation and table bases share the default inherited line width
def WriteInheritedWidth(Writer: ArchiveWriter) -> None:
    Writer.i16(0)
    Writer.f32(-1.0)


def WriteAnnotBase(
    Writer: ArchiveWriter,
    Generation: int,
    Font: PlainCharFormat,
    *,
    UseDocumentBend: bool = True,
    BendDistance: float = 0.00635,
) -> None:
    Writer.i32(4)  # base standard
    Writer.f64(BendDistance)
    Writer.i32(UseDocumentBend)
    Writer.i32(0)  # justification
    Writer.i32(0)  # leader side
    Writer.i32(0)  # leader style
    Writer.i32(0)  # frame font style
    Writer.i32(0)  # leader font style
    Writer.i16(-1)  # no layer object
    for _ in range(2):
        WriteInheritedWidth(Writer)
    WritePlainCharFormat(Writer, Generation, Font)
    Writer.i32(0)  # automatic balloon leader style


def WriteAnnotHeader(Writer: ArchiveWriter) -> None:
    Writer.i32(4)  # base standard
    Writer.f64(0.00635)  # document bend distance
    Writer.i32(0)  # bend mode
    Writer.i32(0)  # edge arrow
    Writer.i32(3)  # face arrow
    Writer.i32(0)  # unattached arrow
    Writer.i32(0)  # leading zero
    Writer.u32(0)  # trailing-zero settings
    Writer.i32(1)  # three-dimensional notes
    Writer.i32(1)  # three-dimensional annotations
    Writer.i32(0)  # show thread type in callout
    Writer.i32(1)  # apply current cosmetic thread appearance to new parts


def WriteBalloonDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(2)  # standard balloon fit
    Writer.i32(2)  # stack balloon fit
    Writer.i32(1)  # stack balloon style
    Writer.i32(1)  # standard balloon style
    Writer.i32(1)  # upper note content
    Writer.i32(2)  # lower note content
    Writer.string("")  # upper note text
    Writer.string("")  # lower note text
    Writer.u32(1)  # balloon options
    Writer.f64(0.01016)  # stack balloon size
    Writer.f64(0.01016)  # standard balloon size
    Writer.i32(0)  # quantity display
    Writer.i32(1)  # quantity placement
    Writer.string("X")  # quantity delimiter
    Writer.f64(0.0)  # standard balloon padding
    Writer.f64(0.0)  # stack balloon padding
    Writer.f64(0.001)  # quantity distance
    Writer.i32(0)  # leader attachment for quantity


def WriteNoteDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(0)  # note balloon fit
    Writer.i32(10)  # note balloon style
    Writer.i32(0)  # leader justification without snapping
    Writer.f64(0.01016)  # note balloon size
    Writer.f64(0.0)  # note balloon padding
    Writer.f64(0.001)  # paragraph spacing
    Writer.i32(1)  # dns period state


def WriteDatumDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(0)  # datum display
    Writer.i32(1)  # gb leader style
    Writer.i32(0)  # unfilled datum
    Writer.i32(1)  # display shoulder
    Writer.i32(0)  # datum label style
    Writer.i32(0)  # 1982 datum mode


def WriteViewLabelDefaults(Writer: ArchiveWriter) -> None:
    Writer.i32(7)  # balloon style
    Writer.i32(9)  # upper note content
    Writer.i32(11)  # lower note content
    Writer.i32(2)  # balloon fit
    Writer.f64(0.01016)
    Writer.i32(1)  # omit the matching sheet number
    Writer.f64(0.0)  # balloon padding
    Writer.i32(0)  # display zone location label


def WriteSavedAnnotations(Writer: ArchiveWriter, Generation: int, Fonts: SavedAnnotationFonts) -> None:
    RequireArch(Generation, 19000, "generation 19000 saved annotation definitions")
    Record = ArchiveWriter()
    WriteAnnotHeader(Record)

    WriteAnnotBase(Record, Generation, Fonts.Standard, UseDocumentBend=False, BendDistance=0.00625)
    WriteBalloonDefaults(Record)

    WriteAnnotBase(Record, Generation, Fonts.Standard)
    WriteNoteDefaults(Record)
    WriteAnnotBase(Record, Generation, Fonts.Standard)
    WriteDatumDefaults(Record)

    WriteAnnotBase(Record, Generation, Fonts.Standard)  # geometric tolerances
    Record.i32(1)  # material condition symbol placement
    Record.i32(1)  # respect drafting standard options
    Record.u16(ord("."))

    WriteAnnotBase(Record, Generation, Fonts.Standard)  # surface finish
    Record.i32(0)  # surface finish size mode
    Record.i32(2)  # iso revision
    Record.f64(1.0)  # symbol scale
    Record.f64(1.0)  # stored second scale

    WriteAnnotBase(Record, Generation, Fonts.Standard)  # weld
    Record.i32(0)  # independent size override
    WritePlainCharFormat(Record, Generation, Fonts.WeldRoot)

    WriteAnnotBase(Record, Generation, Fonts.Standard)  # bend note
    Record.i32(0)  # balloon fit
    Record.i32(0)  # balloon style
    Record.i32(0)  # leader justification without snapping
    Record.f64(0.01016)  # balloon size

    WriteAnnotBase(Record, Generation, Fonts.Standard)  # default annotation
    WriteAnnotBase(Record, Generation, Fonts.RevisionCloud, BendDistance=0.00625)
    Record.f64(0.00508)  # revision cloud maximum radius
    WriteAnnotBase(Record, Generation, Fonts.Standard, UseDocumentBend=False, BendDistance=0.00625)
    WriteViewLabelDefaults(Record)

    Writer.raw(Record.build())
