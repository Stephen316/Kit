from dataclasses import dataclass

from ConfigAnnotations import WriteInheritedWidth
from ConfigDetailOpening import PlainCharFormat, WritePlainCharFormat
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedLabelFonts:
    Label: PlainCharFormat
    Auxiliary: PlainCharFormat
    Orthographic: PlainCharFormat
    Component: PlainCharFormat
    Shared: PlainCharFormat


@dataclass(frozen=True, slots=True, kw_only=True)
class LabelStyle:
    Name: int
    Syntax: int
    EntityLineStyle: int = 0
    EntityLineWeight: int = 0
    AngleName: int = 0


def WriteLabelBase(
    Writer: ArchiveWriter,
    Generation: int,
    Style: LabelStyle,
    Font: PlainCharFormat,
    Component: PlainCharFormat,
) -> None:
    Writer.i32(Style.Name)
    Writer.i32(Style.Syntax)
    Writer.i32(1)  # scale delimiter
    Writer.i32(1)  # scale name
    Writer.i32(1)  # default label visibility
    Writer.i32(0)  # inline label
    Writer.i32(0)  # label above view
    Writer.i32(0)  # add location label
    Writer.i32(4)  # base standard
    Writer.i32(Style.EntityLineStyle)
    Writer.i32(0)  # view border line style
    Writer.i16(-1)  # not assigned to a layer
    Writer.string("")  # custom name
    Writer.string("")  # custom scale text
    Writer.u32(1 << 2)  # clockwise view label
    Writer.i32(Style.AngleName)
    Writer.i32(0)  # view indicator
    for _ in range(2):
        WritePlainCharFormat(Writer, Generation, Font)
    Writer.i16(Style.EntityLineWeight)
    Writer.f32(-1.0)
    WriteInheritedWidth(Writer)
    for _ in range(4):
        WritePlainCharFormat(Writer, Generation, Component)


def WriteSavedLabels(Writer: ArchiveWriter, Generation: int, Fonts: SavedLabelFonts) -> None:
    Record = ArchiveWriter()
    Record.i32(1)  # section label
    Record.i32(1)  # detail label

    WriteLabelBase(Record, Generation, LabelStyle(Name=2, Syntax=1), Fonts.Label, Fonts.Component)
    Record.u32((1 << 3) | (1 << 4))  # dimensions and cosmetic threads follow the parent
    Record.i32(0)  # detail style

    Section = LabelStyle(Name=2, Syntax=2, EntityLineStyle=1, EntityLineWeight=2)
    WriteLabelBase(Record, Generation, Section, Fonts.Label, Fonts.Component)
    Record.f64(0.00635)  # section arrow width
    Record.f64(0.002032)  # section arrow height
    Record.f64(0.0127)  # section arrow length
    Record.i32(0)  # scale with text height
    Record.i32(0)  # alternate section treatment
    Record.i32(0)  # section arrow style
    Record.i32(1)  # half-section arrow
    Record.i32(1)  # hide cutting-plane shoulders

    Auxiliary = LabelStyle(Name=1, Syntax=1, AngleName=1)
    WriteLabelBase(Record, Generation, Auxiliary, Fonts.Auxiliary, Fonts.Component)
    Record.i32(1)  # simplified auxiliary view

    WritePlainCharFormat(Record, Generation, Fonts.Shared)
    for _ in range(2):  # orthographic and miscellaneous share the native ortho serializer
        WriteLabelBase(Record, Generation, LabelStyle(Name=0, Syntax=0), Fonts.Orthographic, Fonts.Component)
        Record.i32(0)  # enable show
        Record.i32(0)  # add label on creation

    Writer.raw(Record.build())
