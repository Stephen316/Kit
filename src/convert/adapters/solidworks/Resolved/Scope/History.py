from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KClassRefKind, ReadTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.OriginProfile import OriginProfile, ReadOrigin
from convert.adapters.solidworks.Resolved.PrincipalDatum import PrincipalDatum
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.Scope.Boss import ScopeBoss, ReadScopedBoss
from convert.adapters.solidworks.Resolved.Scope.Profile import ReadScopeProf
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


# the validated resolved history leaves the cut reader its own feature boundary
@Dataclass(frozen=True, slots=True)
class ScopeHistory:
    Cursor: ArchiveCursor
    Origin: OriginProfile
    Planes: tuple[PrincipalDatum, ...]
    First: ScopeBoss
    Second: ScopeBoss


# the two boss histories must close against the reached map before exposing the next profile
def ReadBossHistory(
    ConfigMap: ArchiveCursor,
    Resolved: bytes,
    Generation: int,
) -> ScopeHistory:
    RequireArch(Generation, KConfigGen, "witnessed scope history generation")
    Cursor = OpenResolved(Resolved, ConfigMap, 23)
    System = ReadSysPrefix(Cursor)
    Origin = ReadOrigin(Cursor, Generation)
    RequireArch(
        Origin.Support.FeatureId,
        System.Planes[0].FeatureId,
        "scoped origin uses the first principal plane",
    )
    FirstProfile = ReadScopeProf(Cursor, Generation, System.Planes, First=True)
    First = ReadScopedBoss(Cursor, FirstProfile, None)
    SecondProfile = ReadScopeProf(Cursor, Generation, System.Planes, First=False)
    Second = ReadScopedBoss(Cursor, SecondProfile, First.Owner.FileObject)
    RequireArch(
        First.Owner.BodyId != Second.Owner.BodyId
        and First.Owner.FeatureId != Second.Owner.FeatureId
        and First.Owner.TransferObject != Second.Owner.TransferObject
        and First.Profile.Sketch.FeatureId != Second.Profile.Sketch.FeatureId,
        True,
        "scoped bosses and their sketches have distinct native identities",
    )
    TagValue = ReadTag(Resolved, Cursor.Offset)
    RequireArch(
        (TagValue.kind, TagValue.wide, Cursor.Classes.get(TagValue.index)),
        (KClassRefKind, False, "moProfileFeature_c"),
        "scope history ends at the next typed profile",
    )
    return ScopeHistory(Cursor, Origin, System.Planes, First, Second)
