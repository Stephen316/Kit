from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.PlaneBasis import (
    KSavedBasis,
    KUnitRows,
    MatrixAxes,
)
from convert.adapters.solidworks.Resolved.BossEntry import (
    BossOperation,
    RectangleBoss,
    ReadRectBoss,
)
from convert.adapters.solidworks.Resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.Resolved.ContourTrim import ReadRectEnd, ReadRectTrim
from convert.adapters.solidworks.Resolved.OriginProfile import OriginProfile, ReadOrigin
from convert.adapters.solidworks.Resolved.PrincipalDatum import PrincipalDatum
from convert.adapters.solidworks.Resolved.PrincipalRef import PrincipalRef
from convert.adapters.solidworks.Resolved.ProfilePlane import (
    CheckProfileRef,
    ReadProfileRef,
)
from convert.adapters.solidworks.Resolved.ProfileSketch import (
    ProfileSketch,
    ReadProfileBody,
)
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


# the neutral projection needs one fully framed sketch and its proven principal datum
@Dataclass(frozen=True, slots=True)
class RectanglePart:
    Profile: ProfileSketch
    Datum: PrincipalDatum
    Reference: PrincipalRef
    Directions: KSavedBasis
    Origin: OriginProfile
    Boss: BossOperation | None


# the datum identity and frame must both agree with the archived sketch attachment
def ResolveDatum(
    Reference: PrincipalRef, Planes: tuple[PrincipalDatum, ...]
) -> tuple[PrincipalDatum, KSavedBasis]:
    for Datum in Planes:
        if Datum.FeatureId != Reference.FeatureId:
            continue
        Geometry = Datum.Geometry
        Directions = CheckProfileRef(
            Reference, Geometry.PointMetres, Geometry.NormalWorld
        )
        Original = MatrixAxes(
            Geometry.BasisValue if Geometry.BasisValue is not None else KUnitRows
        )
        RequireArch(Directions, Original, "sketch transform uses the saved datum axes")
        RequireArch(
            Reference.ShiftScale,
            Geometry.ShiftScale,
            "sketch transform uses the saved datum origin",
        )
        return Datum, Directions
    raise ArchiveError("sketch support does not resolve an earlier principal plane")


# sketch qualification survives a later extrusion outside the supported operation layout
def TryRectBoss(
    Cursor: ArchiveCursor, ProfileObject: int, FileObject: int, TransferObject: int
) -> RectangleBoss | None:
    try:
        return ReadRectBoss(Cursor, ProfileObject, FileObject, TransferObject)
    except ArchiveError:
        return None


# a typed rectangle must own the contour and reach the surrounding feature boundary
def ReadRectPart(ConfigData: bytes, Resolved: bytes, Generation: int) -> RectanglePart:
    ConfigMap, MapWalk = ReadOrdinaryMap(ConfigData, Generation)
    HasAtom = MapWalk["atom_count"] == 1
    Cursor = OpenResolved(Resolved, ConfigMap, 19 if HasAtom else 18)
    System = ReadSysPrefix(Cursor)
    Origin = ReadOrigin(Cursor, Generation)
    RequireArch(
        Origin.Support.FeatureId,
        System.Planes[0].FeatureId,
        "origin resolves the front plane",
    )
    Profile = ReadProfileBody(Cursor, Generation)
    EdgeIds = tuple(
        LineValue["native_id"]
        for LineValue in Profile.Geometry["lines"]
        if LineValue["native_id"] >= 0
    )
    _ = ReadChainState(Cursor, HasAtom, EdgeIds)
    Reference = ReadProfileRef(Cursor, Generation)
    Datum, Directions = ResolveDatum(Reference, System.Planes)
    TrimValue = ReadRectTrim(
        Cursor,
        {"profile_object": Profile.ObjectIndex, "native_feature_id": Profile.FeatureId},
        EdgeIds,
        int(HasAtom),
    )
    _ = ReadRectEnd(Cursor, HasAtom)
    BossValue = None
    if HasAtom:
        TryAtoms = tuple(
            Index
            for Index, ClassName in ConfigMap.Objects.items()
            if ClassName == "moAtom_c"
        )
        if len(TryAtoms) == 1:
            FileObject = TrimValue["trim_surface"]["file_reference"]["object_index"]
            BossValue = TryRectBoss(
                Cursor, Profile.ObjectIndex, FileObject, TryAtoms[0]
            )
    return RectanglePart(Profile, Datum, Reference, Directions, Origin, BossValue)
