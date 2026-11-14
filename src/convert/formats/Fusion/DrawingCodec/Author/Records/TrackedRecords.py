from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KZeroGuid,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget
from convert.formats.Fusion.DrawingCodec.Author.Model.TrackedEdge import TrackedEdge
from convert.formats.Fusion.DrawingCodec.Author.Records.RecordTools import (
    MakeRecord,
    ObjectTail,
)
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KElementGuid = "9899B041-996B-477C-A815-EFAE79D94CBF"

KRecipeBase = "70F5E801-1E8E-436E-8A09-36487F8A2859"

KScopeGuid = "E75C74EA-DD4C-47E1-8EFB-4AA4F8A7D51A"


def TrackedRecords(
    FirstId: int, EdgeValue: TrackedEdge, Design: DesignTarget
) -> tuple[EntityRecord, ...]:
    Entity = (
        NamedValue("m_rCache", None),
        NamedValue("m_rOccurrenceRecipe", None),
        NamedValue("m_rTrackedElement", LocalRef(FirstId + 1)),
    )
    BodyFields = (
        NamedValue("bodyPersistentId", Design.BodyPersistentId),
        NamedValue("version", Design.BodyVersion),
    )
    Recipe = (NamedValue("m_Recipe", OptionalValue(EdgeValue.Recipe)),)
    return (
        MakeRecord(
            FirstId,
            (EntityGroup("77102857-FEA3-4B85-8608-3AEF9C8ABF37", Entity),)
            + ObjectTail(LocalRef(24)),
        ),
        MakeRecord(
            FirstId + 1,
            (
                EntityGroup("E4761EB7-1694-472F-BAC0-24B430387180", BodyFields),
                ElementGroup(FirstId + 5, LocalRef(FirstId + 2)),
            ),
        ),
        OccurRecord(FirstId + 2),
        ScopeRecord(FirstId + 3, Design),
        PathRecord(FirstId + 4),
        MakeRecord(
            FirstId + 5,
            (
                EntityGroup("7ACC2A03-0261-4879-A14A-A93D661A5BDC", Recipe),
                EntityGroup(KRecipeBase, ()),
            ),
        ),
    )


def ElementGroup(RecipeId: int, Target: LocalRef | None) -> EntityGroup[KEntityValue]:
    return EntityGroup(
        KElementGuid,
        (
            NamedValue("m_rRecipe", LocalRef(RecipeId)),
            NamedValue("m_rTargetOccurrence", Target),
        ),
    )


def ScopeValue(AssetId: str, Ident: str, ScopeKind: int) -> ValueObject[KEntityValue]:
    Fields = (
        NamedValue("assetId", AssetId),
        NamedValue("scopeEntityIdentifier", Ident),
        NamedValue("scopeIdType", ScopeKind),
        NamedValue("segmentId", 0),
    )
    return ValueObject((EntityGroup(KScopeGuid, Fields),))


def OccurRecord(ObjectId: int) -> EntityRecord:
    Fields = (NamedValue("m_scope", ScopeValue(KZeroGuid, "", 1)),)
    return MakeRecord(
        ObjectId,
        (
            EntityGroup("7CAA6A9D-984D-487B-8C3D-D45A2448431F", Fields),
            ElementGroup(ObjectId + 2, None),
        ),
    )


def ScopeRecord(ObjectId: int, Design: DesignTarget) -> EntityRecord:
    Fields: tuple[NamedValue[KEntityValue], ...] = (
        NamedValue("instanceIdentifiers", ValueSeries(())),
        NamedValue("passiveLeafComponent", ScopeValue(KZeroGuid, "", 1)),
        NamedValue("scope", ScopeValue(Design.AssetId, Design.ComponentGuid, 2)),
        NamedValue("srcRestructurePaths", ValueSeries(())),
    )
    return MakeRecord(
        ObjectId,
        (
            EntityGroup("96CBEA21-17E0-4BCB-BA77-04EA87B47934", Fields),
            EntityGroup(KRecipeBase, ()),
        ),
    )


def PathRecord(ObjectId: int) -> EntityRecord:
    Fields = (
        NamedValue("isRelativePath", False),
        NamedValue("m_assetOccRecipe", ValueSeries((LocalRef(ObjectId - 1),))),
    )
    return MakeRecord(
        ObjectId,
        (
            EntityGroup("FF415D89-A1DB-44AC-B824-E9A772B86ED4", Fields),
            EntityGroup(KRecipeBase, ()),
        ),
    )
