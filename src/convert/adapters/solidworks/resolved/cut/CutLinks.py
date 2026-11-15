from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.config.CutConfig import CutConfig
from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ArchiveError,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.BossEnd import BossClose, ReadBossClose
from convert.adapters.solidworks.resolved.BossEntry import (
    BossHead,
    ReadBossHead,
    ReadOpNode,
)
from convert.adapters.solidworks.resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.resolved.ContourTrim import ReadRectTrim
from convert.adapters.solidworks.resolved.cut.LinkedProfile import (
    LinkedProfile,
    ReadLinkedProf,
)
from convert.adapters.solidworks.resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.resolved.PrincipalDatum import PrincipalDatum
from convert.adapters.solidworks.resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.resolved.RectanglePart import ResolveDatum
from convert.adapters.solidworks.resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.resolved.SystemPrefix import ReadSysPrefix

# the loaded rectangle boss and cut belong to this observed resolved list shape
KCutListCount = 21


# the cut profile must be reached through its actual earlier rectangle and boss
@Dataclass(frozen=True, slots=True)
class CutLinks:
    Cursor: ArchiveCursor
    Rectangle: LinkedProfile
    BossValue: BossHead
    BossEnd: BossClose
    CutProfile: LinkedProfile


# the first profile chain must cover the configuration rectangle and its saved principal support
def ReadLinkTrim(
    Cursor: ArchiveCursor,
    Config: CutConfig,
    Profile: LinkedProfile,
    Planes: tuple[PrincipalDatum, ...],
) -> int:
    Sketch = Config.Sketches.get(Profile.SketchIndex)
    if Sketch is None:
        raise ArchiveError("missing rectangle configuration sketch")
    Edges = tuple(
        ItemValue["native_id"]
        for ItemValue in Sketch.SketchData.Geometry["lines"]
        if ItemValue["native_id"] >= 0
    )
    _ = ReadChainState(Cursor, True, Edges)
    Reference = ReadProfileRef(Cursor, KConfigGen)
    _ = ResolveDatum(Reference, Planes)
    TrimValue = ReadRectTrim(
        Cursor,
        {"profile_object": Profile.ObjectIndex, "native_feature_id": Profile.FeatureId},
        Edges,
        1,
    )
    return TrimValue["trim_surface"]["file_reference"]["object_index"]


# both resolved names must corroborate the configured equation owners
def CheckCutLinks(
    Config: CutConfig, Rectangle: LinkedProfile, CutProfile: LinkedProfile
) -> None:
    for Equation in Config.Equations:
        RequireArch(
            (Equation.OuterTerm.SketchIndex, Equation.OuterTerm.SketchName),
            (Rectangle.SketchIndex, Rectangle.NameValue),
            "equation outer term resolves to the earlier profile",
        )
        RequireArch(
            (Equation.Target.SketchIndex, Equation.Target.SketchName),
            (CutProfile.SketchIndex, CutProfile.NameValue),
            "equation target resolves to the cut profile",
        )


# the verified prefix leaves the shared cursor at the next bound cut profile field
def ReadCutLinks(BlobValue: bytes, Config: CutConfig) -> CutLinks:
    Cursor = OpenResolved(BlobValue, Config.Cursor, KCutListCount)
    System = ReadSysPrefix(Cursor)
    Origin = ReadOrigin(Cursor, KConfigGen)
    RequireArch(
        Origin.Support.FeatureId,
        System.Planes[0].FeatureId,
        "origin resolves first principal plane",
    )
    Rectangle = ReadLinkedProf(Cursor, KDefinitionKind)
    FileObject = ReadLinkTrim(Cursor, Config, Rectangle, System.Planes)
    NodeValue = ReadOpNode(
        Cursor,
        "moExtrusion_c",
        (0x40000140, 0xC0000140),
        Rectangle.ObjectIndex,
        FileObject,
    )
    BossValue = ReadBossHead(Cursor, NodeValue, (0,))
    RequireArch(
        Config.Cursor.Objects.get(BossValue["transfer_object"]),
        "moAtom_c",
        "earlier configured boss atom reference",
    )
    BossEnd = ReadBossClose(Cursor)
    CutProfile = ReadLinkedProf(Cursor, KClassRefKind)
    CheckCutLinks(Config, Rectangle, CutProfile)
    return CutLinks(Cursor, Rectangle, BossValue, BossEnd, CutProfile)
