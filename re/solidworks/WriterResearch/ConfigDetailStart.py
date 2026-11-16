from dataclasses import dataclass

from ConfigDetailOpening import (
    DetailOpening,
    PlainCharFormat,
    WriteDetailOpening,
    WritePlainCharFormat,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class DetailNames:
    MicrometreSuffix: str
    StatusLabels: tuple[str, str, str, str, str]


@dataclass(frozen=True, slots=True, kw_only=True)
class DetailDimSettings:
    ArrowsOut: int
    SmartArrows: bool
    AddParentheses: bool


def WriteSheetNotes(Writer: ArchiveWriter) -> None:
    # legacy swift tolerancing uses its original selector and constructor tolerances
    Writer.i32(1)
    Writer.f64(0.0005)
    Writer.f64(0.008726646259971667)
    Writer.i32(1)

    Writer.i32(0)  # bend note style
    Writer.i32(1)  # show sheet metal bend notes
    Writer.i32(1)  # simplify bends
    Writer.i32(1)  # corner treatment
    Writer.i32(1)  # disable splitters
    Writer.i32(1)  # show flattened punches
    Writer.i32(0)  # show flattened profiles
    Writer.i32(0)  # show flattened centers


def WriteCenterMarks(Writer: ArchiveWriter) -> None:
    Writer.u8(0)  # automatic fillet center marks
    Writer.i32(1)  # slot dimensions for power assist
    Writer.i32(0)  # chamfer dimensions for power assist
    Writer.i32(0)  # chamfer instance display
    Writer.i32(0)  # fillet instance display
    Writer.u8(0)  # automatic assembly hole center marks
    Writer.u8(0)  # automatic assembly fillet center marks
    Writer.i16(-1)  # no centerline layer
    Writer.i16(-1)  # no center mark layer
    Writer.i32(1)  # automatic dowel symbol
    Writer.i32(0)  # automatic assembly dowel symbol
    Writer.f64(0.008)  # center-of-mass symbol size
    Writer.i32(0)  # center-of-mass symbol scales by view


def WriteSheetAndWeldment(Writer: ArchiveWriter) -> None:
    Writer.string("")  # sheet format path
    Writer.i32(0)  # sheet format selector
    Writer.string("")  # full sheet format path
    Writer.i32(1)  # sheet format path validity
    Writer.i32(0)  # show flattened gusset profiles
    Writer.i32(0)  # show flattened gusset centers
    Writer.i32(0)  # override sheet metal template parameters
    Writer.i32(0)  # override sheet metal template allowance
    Writer.i32(0)  # override sheet metal template relief
    Writer.i32(0)  # use sheet metal material
    Writer.i32(1)  # highlight associated dimension elements
    Writer.i32(1)  # automatic cut list
    Writer.i32(1)  # automatic cut list update
    Writer.i32(1)  # inherit description property
    Writer.i32(1)  # disable derived configuration
    Writer.i32(1)  # disable weldment configuration strings


def WriteDetailNames(Writer: ArchiveWriter, Names: DetailNames) -> None:
    Exclusions = ("m", "mm", "cm", "km", "um", Names.MicrometreSuffix, "nm", "s", "Hz", "Pa")
    Writer.i32(len(Exclusions))
    for Name in Exclusions:
        Writer.string(Name)

    Writer.i32(1)  # rename the structural member name
    Writer.i32(0)  # custom property column widths are unset
    Writer.i32(0)  # cut list column widths are unset
    Writer.zeros(2 * 3 * 8 * 4)  # two unset 3-by-8 signed-width tables

    Writer.u16(len(Names.StatusLabels))
    for Label in Names.StatusLabels:
        Writer.string(Label)


# the selector-4 setup and native constructor supply these dimension distances
def WriteDimSettings(Writer: ArchiveWriter, Settings: DetailDimSettings) -> None:
    Writer.i32(4)  # base standard
    Writer.f64(0.001016)  # arrow height
    Writer.f64(0.003302)  # arrow width
    Writer.f64(0.00635)  # arrow length
    Writer.f64(0.001)  # witness gap
    Writer.f64(0.001)  # witness extension
    Writer.f64(0.005)  # ordinate jog size
    Writer.f64(0.01)  # break distance
    Writer.f64(0.003175)  # break line extension
    Writer.f64(0.001524)  # dimension break gap
    Writer.f64(0.00635)  # dimension extra leader distance
    Writer.f64(-25.0)  # maximum witness length
    Writer.i32(Settings.ArrowsOut)
    Writer.i32(0)  # break around arrows only
    Writer.i32(0)  # arrow style
    Writer.i32(20)  # dimension offset count
    Writer.i32(Settings.SmartArrows)
    Writer.f64(0.0)  # secondary tolerance minimum
    Writer.f64(0.0)  # secondary tolerance maximum
    Writer.i32(0)  # secondary tolerance style
    Writer.i32(0)  # scale with dimension height
    Writer.f64(0.01)  # first dimension distance
    Writer.f64(0.006)  # second dimension distance
    Writer.f64(0.26179938779915)  # radial dimension snap angle

    # show broken dimensions, follow model layout and show dimension/tolerance trailing zeros
    Flags = (1 << 4) | (1 << 5) | (1 << 7) | (1 << 13)
    Writer.u32(Flags | Settings.AddParentheses)
    Writer.i32(1)  # dimension fraction style
    Writer.f64(1.0)  # dimension fraction scale
    Writer.i32(0)  # leading zero
    Writer.i32(1)  # double prime mark
    Writer.i32(1)  # extend leader to text
    Writer.i32(1)  # show broken dimensions in model break view
    Writer.i32(1)  # dimension arrow 1
    Writer.i32(1)  # dimension arrow 2
    Writer.i32(1)  # modern dimension default field


def WriteDetailStart(
    Writer: ArchiveWriter,
    Generation: int,
    Opening: DetailOpening,
    Names: DetailNames,
    Font: PlainCharFormat,
    Dimensions: DetailDimSettings,
) -> None:
    RequireArch(
        type(Names.StatusLabels) is tuple
        and len(Names.StatusLabels) == 5
        and all(
            isinstance(Value, str) and Value and "\x00" not in Value
            for Value in (Names.MicrometreSuffix, *Names.StatusLabels)
        ),
        True,
        "nonempty detail resource labels",
    )
    RequireArch(
        type(Dimensions.ArrowsOut) is int
        and Dimensions.ArrowsOut == 2
        and type(Dimensions.SmartArrows) is bool
        and type(Dimensions.AddParentheses) is bool,
        True,
        "supported detail dimension settings",
    )

    # all owners in this interval serialize inline without touching the part map
    Record = ArchiveWriter()
    WriteDetailOpening(Record, Generation, Opening)
    WriteSheetNotes(Record)
    WriteCenterMarks(Record)
    WriteSheetAndWeldment(Record)
    WriteDetailNames(Record, Names)
    WritePlainCharFormat(Record, Generation, Font)
    WriteDimSettings(Record, Dimensions)
    Writer.raw(Record.build())
