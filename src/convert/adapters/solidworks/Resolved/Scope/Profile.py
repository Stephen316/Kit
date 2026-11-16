from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.PlaneBasis import KSavedBasis
from convert.adapters.solidworks.Resolved.ContourChain import ProfileChain, ReadChain
from convert.adapters.solidworks.Resolved.PrincipalDatum import PrincipalDatum
from convert.adapters.solidworks.Resolved.PrincipalRef import PrincipalRef
from convert.adapters.solidworks.Resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.Resolved.ProfileSketch import (
    ProfileSketch,
    ReadProfileBody,
)
from convert.adapters.solidworks.Resolved.RectanglePart import ResolveDatum


# the saved chain and principal reference keep the authored boss sketch attached
@Dataclass(frozen=True, slots=True)
class ScopeProfile:
    Sketch: ProfileSketch
    Chain: ProfileChain
    Reference: PrincipalRef
    Datum: PrincipalDatum
    Directions: KSavedBasis
    TrimState: int
    End: int


# both scoped sketches have their own contour mode and no saved trim geometry
def ReadScopeTrim(Cursor: ArchiveCursor, ModeValue: int) -> int:
    RequireArch(Cursor.ReadInts("<2H"), (0, 4), "witnessed scoped profile flags")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2i"), (-1, 0), "witnessed scoped profile state")
    (State,) = Cursor.ReadInts("<I")
    RequireArch(Cursor.ReadInts("<H"), (ModeValue,), "witnessed scoped contour mode")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2Hi"), (0, 0, 0), "empty scoped trim geometry cache")
    return State


# scope support is resolved by the saved plane identity and basis instead of its name
def ReadScopeProf(
    Cursor: ArchiveCursor,
    Generation: int,
    Planes: tuple[PrincipalDatum, ...],
    *,
    First: bool,
) -> ScopeProfile:
    KindValue = KDefinitionKind if First else KClassRefKind
    Sketch = ReadProfileBody(
        Cursor, Generation, ProfileKind=KindValue, EnvironmentLead=6 if First else 5
    )
    EdgeIds = tuple(
        LineValue["native_id"]
        for LineValue in Sketch.Geometry["lines"]
        if LineValue["native_id"] >= 0
    )
    RequireArch(
        len(EdgeIds) == len(set(EdgeIds)) == 4,
        True,
        "four distinct scoped sketch edges",
    )
    RequireArch(Cursor.ReadInts("<Ii"), (1, 1), "one saved scoped profile chain")
    Chain = ReadChain(Cursor, KindValue)
    RequireArch(
        sorted(Chain["edge_ids"]), sorted(EdgeIds), "scoped chain covers its sketch"
    )
    Reference = ReadProfileRef(Cursor, Generation)
    Datum, Directions = ResolveDatum(Reference, Planes)
    State = ReadScopeTrim(Cursor, 1 if First else 3)
    return ScopeProfile(
        Sketch, Chain, Reference, Datum, Directions, State, Cursor.Offset
    )
