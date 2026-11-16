from dataclasses import dataclass
from struct import pack as Pack

from ConfigDetailOpening import PlainCharFormat, WritePlainCharFormat
from ConfigUnitFields import WriteUnitFields
from ConfigUnits import KLengthClass
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import EncodeNull, KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedStyleSettings:
    LengthUnit: int
    LinearPrevious: float
    Font: PlainCharFormat


@dataclass(frozen=True, slots=True, kw_only=True)
class DimensionStyle:
    Name: str
    TailFormat: str = ""
    TailFields: tuple[int | float, ...] = ()
    AngularUnits: bool = False
    DualUnits: bool = True
    VerticalAlignment: int = 1
    Leader: int = 0
    AlternateTolerancePlaces: int = 3
    DualOnSameLine: bool = False


# the dimension definitions file these inline style objects in native call order
KDimensionStyles = (
    DimensionStyle(Name="moLinearDimDef_c", TailFormat="<I2i", TailFields=(0, 2, 0)),
    DimensionStyle(
        Name="moAngleDimDef_c",
        TailFormat="<I",
        TailFields=(0x142,),
        AngularUnits=True,
        DualUnits=False,
    ),
    DimensionStyle(Name="moArcLengthDimDef_c"),
    DimensionStyle(Name="moRadialDimDef_c", TailFormat="<Ii", TailFields=(2, 1)),
    DimensionStyle(
        Name="moHoleCalloutDimDef_c",
        TailFormat="<I",
        TailFields=(0,),
        DualOnSameLine=True,
    ),
    DimensionStyle(Name="moOrdinateDimDef_c", TailFormat="<iId", TailFields=(1, 1, 0.0015875)),
    DimensionStyle(
        Name="moChamferDimDef_c",
        TailFormat="<4i2d2i",
        TailFields=(0, 1, 2, 2, 0.0, 0.0, 0, 0),
        VerticalAlignment=2,
        Leader=3,
        DualOnSameLine=True,
    ),
    DimensionStyle(Name="moDiameterDimDef_c", TailFormat="<iI", TailFields=(1, 0)),
    DimensionStyle(
        Name="moAngOrdinateDimDef_c",
        TailFormat="<iI3i",
        TailFields=(1, 0x15, 0, 0, 0),
        AngularUnits=True,
        AlternateTolerancePlaces=2,
    ),
    DimensionStyle(Name="moBaseDimDef_c"),
)


def WriteBaseStyle(Writer: ArchiveWriter, Style: DimensionStyle) -> None:
    Writer.i32(4)  # base standard
    Writer.i32(1)  # horizontal text alignment
    Writer.i32(Style.VerticalAlignment)
    Writer.f64(1.0)  # tolerance text scale
    Writer.f64(0.0127)  # tolerance text height
    Writer.i32(1)  # use tolerance text scale
    Writer.f64(1.0)  # fit tolerance text scale
    Writer.f64(0.0127)  # fit tolerance text height
    Writer.i32(1)  # use fit tolerance text scale
    Writer.i32(0)  # tolerance style
    Writer.string("")  # upper tolerance override
    Writer.string("")  # lower tolerance override
    Writer.f64(0.0)  # tolerance minimum
    Writer.f64(0.0)  # tolerance maximum
    Writer.i32(1)  # fit strategy
    Writer.i32(Style.Leader)
    Writer.i32(1)  # fit style
    Writer.i32(0)  # tolerance parentheses
    Writer.i32(2)  # dimension decimal places
    Writer.i32(2)  # alternate dimension decimal places
    Writer.i32(2)  # tolerance decimal places
    Writer.i32(Style.AlternateTolerancePlaces)
    Writer.i16(-1)  # no layer object
    Writer.i32(Style.DualOnSameLine)
    Writer.i32(0)  # no bent leader
    Writer.u32((1 << 6) | (1 << 7))  # dimension precision supplies primary and dual tolerance precision


def WriteStyleUnits(Writer: PartArchiveWriter, Style: DimensionStyle, State: SavedStyleSettings) -> None:
    if Style.AngularUnits:
        WriteUnitFields(Writer, "common")
        Writer.u16(2)
    else:
        Previous = State.LinearPrevious if Style.Name == "moLinearDimDef_c" else 0.0
        WriteUnitFields(Writer, "primary", Previous)
        Writer.u16(State.LengthUnit)

    if Style.DualUnits:
        Writer.BeginObject(KLengthClass, 1)
        WriteUnitFields(Writer, "dual")
        Writer.u16(3)
    Writer.raw(EncodeNull())
    WriteUnitFields(Writer, "common")
    Writer.u16(0)  # the inline angle formatter uses the measured angle selector


def WriteStyleAppearance(Writer: ArchiveWriter, Font: bytes) -> None:
    Writer.raw(Font)
    for _ in range(2):  # leader and extension line fonts are separate inline owners
        Writer.string("CONTINUOUS")
        Writer.i16(0)
        Writer.f32(-1.0)
        Writer.i16(0)
    Writer.i32(1)  # extension line properties follow the leader
    Writer.i32(0)  # inward range tolerance is unset
    Writer.i32(0)  # remove zero is unset


def WriteSavedDimensionStyles(Writer: PartArchiveWriter, Generation: int, State: SavedStyleSettings) -> None:
    RequireArch(
        type(State.LengthUnit) is int
        and State.LengthUnit in (0, 3)
        and type(State.LinearPrevious) in (int, float)
        and State.LinearPrevious in (0.0, 20.0),
        True,
        "measured style length units and independent previous linear value",
    )
    Count = sum(Style.DualUnits for Style in KDimensionStyles)
    RequireArch(
        0 < Writer.classes.get(KLengthClass, 0) < Writer.next_index and Writer.next_index + Count <= KBigObjectTag,
        True,
        "existing length unit class and available allocation slots",
    )
    FontWriter = ArchiveWriter()
    WritePlainCharFormat(FontWriter, Generation, State.Font)
    Font = FontWriter.build()
    for Style in KDimensionStyles:
        WriteBaseStyle(Writer, Style)
        WriteStyleUnits(Writer, Style, State)
        WriteStyleAppearance(Writer, Font)
        if Style.TailFormat:
            Writer.raw(Pack(Style.TailFormat, *Style.TailFields))
