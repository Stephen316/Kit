from dataclasses import dataclass
from math import isfinite as IsFinite

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@dataclass(frozen=True, slots=True, kw_only=True)
class DetailPrecision:
    Digits: tuple[int, int, int]
    Tolerances: tuple[float, float, float]


@dataclass(frozen=True, slots=True, kw_only=True)
class DetailOpening:
    CenterMarkSize: float
    CenterMarkUseLines: bool
    UseTableTemplateSettings: bool
    DisplayGraphicBodiesInDrawingViews: bool
    CenterLineUseCenterline: bool
    VirtualSharpType: int
    CenterLineDistance: float
    AutoCenterMarkHoles: bool
    AutoInsertCenterLine: bool
    AutoUpdateBom: bool
    AutoDesignIntent: bool
    CenterMarkUseCenterLine: bool
    UseNewCThreadDisplay: bool
    Linear: DetailPrecision
    Angular: DetailPrecision


def ValidatePrecision(Value: DetailPrecision) -> None:
    RequireArch(
        (type(Value.Digits), type(Value.Tolerances)),
        (tuple, tuple),
        "saved detail precision groups are tuples",
    )
    RequireArch(
        (len(Value.Digits), len(Value.Tolerances)),
        (3, 3),
        "three saved entries per detail precision group",
    )
    RequireArch(
        all(type(Digits) is int and 0 <= Digits <= 0xFFFFFFFF for Digits in Value.Digits)
        and all(IsFinite(Tolerance) and Tolerance >= 0 for Tolerance in Value.Tolerances),
        True,
        "three detail precisions and their nonnegative tolerances",
    )


# The inline model array is empty and the saved base standard has no custom name.
def WriteDetailOpening(Writer: ArchiveWriter, Generation: int, State: DetailOpening) -> None:
    RequireArch(Generation, 19000, "generation 19000 detail opening")
    RequireArch(
        IsFinite(State.CenterMarkSize)
        and State.CenterMarkSize > 0
        and IsFinite(State.CenterLineDistance)
        and State.CenterLineDistance >= 0
        and type(State.VirtualSharpType) is int
        and State.VirtualSharpType == 2,
        True,
        "supported center mark, center line and virtual sharp settings",
    )
    Flags = (
        State.UseTableTemplateSettings,
        State.DisplayGraphicBodiesInDrawingViews,
        State.CenterLineUseCenterline,
    )
    Options = (
        State.AutoCenterMarkHoles,
        State.AutoInsertCenterLine,
        State.AutoUpdateBom,
        State.AutoDesignIntent,
        State.CenterMarkUseCenterLine,
    )
    RequireArch(
        all(
            type(Value) is bool
            for Value in (
                State.CenterMarkUseLines,
                State.UseNewCThreadDisplay,
                *Flags,
                *Options,
            )
        ),
        True,
        "boolean detail settings",
    )
    ValidatePrecision(State.Linear)
    ValidatePrecision(State.Angular)

    Writer.u16(0)
    Writer.i32(4)
    Writer.string("")
    Writer.f64(State.CenterMarkSize)
    Writer.u8(State.CenterMarkUseLines)
    Writer.u32(sum(Flag << Bit for Flag, Bit in zip(Flags, (14, 18, 20), strict=True)))
    Writer.i32(State.VirtualSharpType)
    Writer.f64(State.CenterLineDistance)
    for Option in Options:
        Writer.u8(Option)
    Writer.i32(State.UseNewCThreadDisplay)
    for Group in (State.Linear, State.Angular):
        for Digits in Group.Digits:
            Writer.u32(Digits)
        for Tolerance in Group.Tolerances:
            Writer.f64(Tolerance)


@dataclass(frozen=True, slots=True, kw_only=True)
class PlainCharFormat:
    Face: str
    Height: float
    LineSpacing: float


# Document preferences provide the face, system-unit height and line spacing.
def WritePlainCharFormat(Writer: ArchiveWriter, Generation: int, State: PlainCharFormat) -> None:
    RequireArch(Generation, 19000, "generation 19000 inline character format")
    RequireArch(
        bool(State.Face)
        and "\x00" not in State.Face
        and IsFinite(State.Height)
        and State.Height > 0
        and IsFinite(State.LineSpacing)
        and State.LineSpacing >= 0,
        True,
        "plain character face, system-unit height and line spacing",
    )
    WriteCharFields(Writer, State.Face, State.Height, State.LineSpacing)


@dataclass(frozen=True, slots=True, kw_only=True)
class UnsetCharFormat:
    Face: str


def WriteUnsetCharFormat(Writer: ArchiveWriter, Generation: int, State: UnsetCharFormat) -> None:
    RequireArch(Generation, 19000, "generation 19000 inline character format")
    RequireArch(
        isinstance(State.Face, str) and bool(State.Face) and "\x00" not in State.Face,
        True,
        "nonempty default annotation face",
    )
    WriteCharFields(Writer, State.Face, -1.0, 0.001)


def WriteCharFields(Writer: ArchiveWriter, Face: str, Height: float, LineSpacing: float) -> None:
    Writer.string(Face)
    Writer.f64(Height)
    Writer.i32(0)
    Writer.f64(0.0)
    Writer.u32(0)
    Writer.f64(LineSpacing)
    Writer.f64(1.0)
    Writer.f64(0.0)
    Writer.f64(0.0)
    Writer.f64(1.0)
    Writer.u32(400)
