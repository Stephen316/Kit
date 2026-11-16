from dataclasses import dataclass as Dataclass
from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossDepth import (
    DepthDisplay,
    DepthReference as SavedDistance,
    ReadDepthRefs,
)
from convert.adapters.solidworks.Resolved.BossEnd import (
    EndSpec,
    ReadEndHead,
    ReadStartHead,
)
from convert.adapters.solidworks.Resolved.PlaneGeom import DatumData
from convert.adapters.solidworks.Resolved.Scope.Distance import (
    KPlaneTolerance,
    PointOffset,
    SignedDistance,
)


# the operation keeps both signed placements and their independent native length sources
@Dataclass(frozen=True, slots=True)
class ScopedExtent:
    EndSpec: EndSpec
    Depth: DepthDisplay
    DepthReference: SavedDistance
    DepthMetres: float
    StartObject: int
    StartMode: int
    Start: DepthDisplay | None
    StartReference: SavedDistance | None
    StartMetres: float
    RawStartWords: tuple[int, ...]
    RawStartToken: bytes | None
    End: int


# the start selector separates the sketch plane from an independently dimensioned offset
def ReadScopeStart(
    Cursor: ArchiveCursor,
    KindValue: str,
    Normal: tuple[float, ...],
    DatumOrigin: tuple[float, ...],
    *,
    First: bool,
) -> tuple[
    int,
    int,
    DepthDisplay | None,
    SavedDistance | None,
    float,
    tuple[int, ...],
    bytes | None,
]:
    StartObject = ReadStartHead(Cursor, KindValue, 0)
    (ModeValue,) = Cursor.ReadInts("<i")
    RequireArch(ModeValue, 0 if First else 5, "witnessed scoped boss start condition")
    if First:
        return StartObject, ModeValue, None, None, 0.0, Cursor.ReadInts("<5i"), None
    Display, Reference = ReadDepthRefs(Cursor, KClassRefKind, DisplayMode=200)
    RequireArch(
        IsClose(
            PointOffset(Reference["points_metres"][:3], DatumOrigin, Normal),
            0.0,
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        ),
        True,
        "offset display starts on the reached sketch support",
    )
    LeadWord, Token, TailWord = CastValue(
        tuple[int, bytes, int], Cursor.ReadValue("<i16si")
    )
    RequireArch((LeadWord, TailWord), (1, 1), "witnessed offset start framing")
    return (
        StartObject,
        ModeValue,
        Display,
        Reference,
        SignedDistance(Display, Reference, Normal),
        (LeadWord, TailWord),
        Token,
    )


# signed extent must agree with both display geometry and the direct native direction field
def ReadBossExtent(
    Cursor: ArchiveCursor,
    Datum: DatumData,
    Centre: tuple[float, ...],
    *,
    First: bool,
) -> ScopedExtent:
    KindValue = KDefinitionKind if First else KClassRefKind
    EndSpec = ReadEndHead(Cursor, KindValue, (0, 1))
    RequireArch(EndSpec["conditions"], (0, 0), "witnessed scoped blind extent")
    Depth, Reference = ReadDepthRefs(
        Cursor,
        KindValue,
        DisplayMode=200,
        DisplayKind=KindValue,
        FavoriteKind=KindValue,
    )
    Normal, Origin = Datum.NormalWorld, Datum.PointMetres
    SignedDepth = SignedDistance(Depth, Reference, Normal)
    RequireArch(
        EndSpec["direction"],
        int(SignedDepth < 0),
        "scope blind direction agrees with its signed distance",
    )
    StartObject, ModeValue, Start, StartRef, Offset, RawWords, Token = ReadScopeStart(
        Cursor, KindValue, Normal, Origin, First=First
    )
    RequireArch(
        IsClose(
            PointOffset(Reference["points_metres"][:3], Origin, Normal),
            Offset,
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        )
        and IsClose(
            PointOffset(Centre[:3], Origin, Normal),
            Offset + SignedDepth / 2,
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        ),
        True,
        "scope blind display and chooser centre agree with the signed start",
    )
    RequireArch(
        Cursor.ReadValue("<di"), (0, -1 if First else 0), "witnessed scoped boss return"
    )
    return ScopedExtent(
        EndSpec,
        Depth,
        Reference,
        SignedDepth,
        StartObject,
        ModeValue,
        Start,
        StartRef,
        Offset,
        RawWords,
        Token,
        Cursor.Offset,
    )
