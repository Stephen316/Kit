from dataclasses import dataclass as Dataclass

from CmgrBaseEnd import WriteCmgrBaseEnd
from CmgrBaseHeader import CmgrBaseState, WriteCmgrHeader
from CmgrBossMass import EncodeBossMass, Point
from CmgrCollectionFront import WriteCmgrFront
from CmgrCollections import WriteCollections
from CmgrExternal import ExternalFile, WriteCmgrExt
from CmgrInherited import WriteCmgrFeature
from CmgrLinks import WriteCmgrLinks
from CmgrMass import EncodeEmptyMass
from CmgrOpening import CmgrOpenFields, WriteCmgrOpening
from CmgrPartEnd import WriteCmgrAliases, WriteCmgrPartEnd
from CmgrTail import WriteCmgrTail
from CmgrVisualPrefix import CmgrVisualFields, WriteCmgrVisualPrefix
from ColorAppearance import EncodeColorDspbr
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import FeatureStamp, Stamp
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


@Dataclass(frozen=True, slots=True)
class CmgrRectangularBoss:
    AtomId: int
    Feature: FeatureStamp
    BodyStamp: int
    MinimumM: Point
    MaximumM: Point
    DensityKgM3: float


@Dataclass(frozen=True, slots=True)
class CmgrDocument:
    Opening: CmgrOpenFields
    Visual: CmgrVisualFields
    PartTime: Stamp
    NextTreeId: int
    SessionStamp: int
    External: ExternalFile
    Boss: CmgrRectangularBoss | None


# Both standalone shapes have one configuration and one external object.
def BuildCmgr(Generation: int, Document: CmgrDocument) -> ArchiveWriter:
    RequireArch(
        (
            type(Generation) is int and Generation == 19000,
            type(Document.NextTreeId) is int and 1 < Document.NextTreeId <= 0x7FFFFFFF,
            Document.External.ConfigName == Document.Opening.NameValue,
        ),
        (True, True, True),
        "CMgr standalone document generation, tree allocator and external configuration",
    )
    Boss = Document.Boss
    if Boss is None:
        AtomIds: tuple[int, ...] = ()
        Links: tuple[tuple[int, int], ...] = ()
        Stamps: tuple[FeatureStamp, ...] = ()
        MassStamp = 0
        Mass = EncodeEmptyMass(Generation, 0)
    else:
        TreeId = Boss.Feature.tree_id
        RequireArch(
            type(TreeId) is int
            and 0 < TreeId < Document.NextTreeId
            and type(Boss.BodyStamp) is int
            and 0 < Boss.BodyStamp <= 0xFFFFFFFF,
            True,
            "CMgr allocated boss feature and body stamp",
        )
        AtomIds = (Boss.AtomId,)
        Links = ((Boss.AtomId, TreeId),)
        Stamps = (Boss.Feature,)
        MassStamp = Boss.BodyStamp
        Mass = EncodeBossMass(
            Generation, 1, Boss.MinimumM, Boss.MaximumM, Boss.DensityKgM3
        )

    Writer = ArchiveWriter()
    Slots = WriteCmgrOpening(Writer, Generation, Document.Opening)
    WriteCmgrVisualPrefix(Writer, Generation, Document.Visual)
    Writer.raw(EncodeColorDspbr(Generation, Document.Visual.SurfaceColor))
    WriteCmgrFeature(Writer, Generation, Document.PartTime)
    WriteCmgrHeader(
        Writer,
        Generation,
        CmgrBaseState(Document.NextTreeId - 1, Document.SessionStamp, MassStamp),
    )
    Writer.raw(Mass)
    WriteCmgrFront(Writer, Generation, BodyCount=len(AtomIds), SaveMode=1)
    WriteCollections(Writer, Generation, AtomIds)
    WriteCmgrLinks(Writer, Generation, Links)
    WriteCmgrBaseEnd(
        Writer,
        Generation=Generation,
        ConditionOne=False,
        AtomCount=len(AtomIds),
        NewThreadRefs=True,
    )
    WriteCmgrPartEnd(Writer, Generation=Generation, ConditionOne=False, AtomIds=AtomIds)
    WriteCmgrAliases(
        Writer,
        Generation=Generation,
        PartIndex=Slots.PartObject,
        PartId=Slots.ConfigId,
        ExternalCount=1,
    )
    WriteCmgrExt(Writer, Generation, Document.External)
    WriteCmgrTail(Writer, Generation, Stamps)
    return Writer
