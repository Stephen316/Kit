from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite

from convert.adapters.solidworks.Container.Archive import KDefinitionKind, KStringMarker
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the part owns a section appearance before it files its distinct material pointer
KHatchClass = "gcXhatch_c"


# the following material is an independent allocation on the part archive map
KPartMaterial = "moMaterial_c"


# the saved section hatch options belong to the part appearance caller
@DataClass(frozen=True)
class SectionHatch:
    Pattern: str
    Angle: float
    Scale: float
    Override: int
    Solid: int
    PatternId: int
    LayerId: int
    CommandColor: int
    RandomizeScale: int


# unsupported hatch identifiers and invalid values must fail before allocation
def RequireHatch(State: SectionHatch) -> None:
    RequireArch(
        bool(State.Pattern) and "\0" not in State.Pattern,
        True,
        "nonempty section hatch pattern",
    )
    RequireArch(
        IsFinite(State.Angle) and IsFinite(State.Scale) and State.Scale > 0.0,
        True,
        "finite hatch angle and positive scale",
    )
    RequireArch(
        (
            State.Override,
            State.Solid,
            State.PatternId,
            State.LayerId,
            State.CommandColor,
            State.RandomizeScale,
        ),
        (0, 0, 1, -1, -1, 0),
        "ordinary unlayered part section hatch",
    )


# the actual hatch definition must allocate before reading its scoped options
def ReadHatch(Cursor: ArchiveCursor) -> SectionHatch:
    Cursor.TakePointer((KHatchClass,), KDefinitionKind, CompactOnly=True)
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset),
        True,
        "wide section hatch pattern",
    )
    Pattern = Cursor.ReadText()
    Angle, Scale = Cursor.ReadPoint(2)
    State = SectionHatch(Pattern, Angle, Scale, *Cursor.ReadInts("<6i"))
    RequireHatch(State)
    return State


# typed hatch fields preserve the model namespace for the upcoming material allocation
def WriteHatch(Writer: ArchiveWriter, State: SectionHatch) -> None:
    Writer.BeginObject(KHatchClass, 1)
    Writer.string(State.Pattern)
    Writer.f64(State.Angle)
    Writer.f64(State.Scale)
    Writer.i32(State.Override)
    Writer.i32(State.Solid)
    Writer.i32(State.PatternId)
    Writer.i32(State.LayerId)
    Writer.i32(State.CommandColor)
    Writer.i32(State.RandomizeScale)
