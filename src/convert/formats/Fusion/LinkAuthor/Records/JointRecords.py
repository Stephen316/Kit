from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.LinkAuthor.MatrixMath import ComposeMatrix, InvertRigid
from convert.formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.ActionGroups import (
    ActionRecords,
    FeatureGroups,
)
from convert.formats.Fusion.LinkAuthor.Records.JointValues import (
    FeatureState,
    JointState,
    OperandValue,
)
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KAssemblyFeature,
    KCommonBase,
    KConstraint,
    KConstraintFeature,
    KConstraintOccurrence,
    KDcConstraintOcc,
    KDcJointFeature,
    KDcJointOccurrence,
    KJoint,
    KJointFeature,
    KJointOccurrence,
    KManagedEntity,
    KZeroGuid,
)
from convert.formats.Fusion.LinkAuthor.Records.PathValues import (
    OccurPath,
    ScopeValue,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    LocalSeries,
    MakeGroup,
    MakeRecord,
)
from convert.formats.Fusion.LinkAuthor.Records.RefRecords import OccurRef, RefRecords
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


@MakeDataClass(frozen=True, slots=True)
class JointSide:
    Facts: TargetFacts
    Place: PlaceKeys
    Matrix: tuple[float, ...]
    Pinned: bool


def JointRecord(
    RootInfo: RootFacts, First: JointSide, Second: JointSide, JointId: int
) -> EntityRecord:
    Alignment = ComposeMatrix(InvertRigid(First.Matrix), Second.Matrix)
    Subjects = (
        SubjectValue(LocalRef(First.Place.Instance), 3 if First.Pinned else 2),
        SubjectValue(LocalRef(Second.Place.Instance), 3 if Second.Pinned else 2),
    )
    Operands = (
        OperandValue(RootInfo, First.Place.InstanceId, Alignment),
        OperandValue(RootInfo, Second.Place.InstanceId, None),
    )
    return FrameRecord(
        JointId,
        EntityFrame("", Subjects, None),
        MakeGroup(
            KJoint,
            *(
                (FieldName, None)
                for FieldName in ("dofRotate0", "dofRotate1", "dofRotate2")
            ),
            *(
                (FieldName, None)
                for FieldName in ("dofSlide0", "dofSlide1", "dofSlide2")
            ),
            ("type", 0),
            ("useConstraintAlignment", False),
        ),
        MakeGroup(
            KConstraint,
            ("creationIndex", 1),
            ("deriveFeature", None),
            ("operandVec", ValueSeries(Operands)),
            ("userName", ""),
        ),
        MakeGroup(KCommonBase, ("rClientObject", None)),
        MakeGroup(KManagedEntity, ("rParent", LocalRef(RootInfo.Constraints))),
    )


def SideRef(
    RootInfo: RootFacts,
    Joined: JointSide,
    Identities: tuple[int, int, int],
    Parent: int,
    Alignment: tuple[float, ...] | None,
) -> OccurRef:
    return OccurRef(
        Identities,
        2,
        Joined.Place.Occurrence,
        Alignment,
        Parent,
        True,
        (Joined.Place.PersistentId,),
        ScopeValue(Joined.Facts.AssetId, Joined.Facts.PersistentId, 2),
        ScopeValue(RootInfo.AssetId, RootInfo.PersistentId, 2),
    )


def SourceRef(
    RootInfo: RootFacts, Identities: tuple[int, int, int], Parent: int
) -> OccurRef:
    return OccurRef(
        Identities,
        0,
        RootInfo.RootOccurrence,
        None,
        Parent,
        False,
        (),
        ScopeValue(KZeroGuid, "", 1),
        ScopeValue(RootInfo.AssetId, RootInfo.PersistentId, 2),
    )


def JointRecords(
    RootInfo: RootFacts, First: JointSide, Second: JointSide, KeySet: ActionKeys
) -> tuple[EntityRecord, ...]:
    if len(KeySet.Extra) != 12:
        raise ValueError("Fusion joint feature plan needs twelve extra identities")
    JointId, FirstA, FirstB, FirstC, SecondA, SecondB, SecondC, *Remaining = (
        KeySet.Extra
    )
    SourceA, SourceB, SourceC, DcOccurId, JointOccId = Remaining
    FirstIds = (FirstA, FirstB, FirstC)
    SecondIds = (SecondA, SecondB, SecondC)
    SourceIds = (SourceA, SourceB, SourceC)
    Alignment = ComposeMatrix(InvertRigid(First.Matrix), Second.Matrix)
    return (
        JointRecord(RootInfo, First, Second, JointId),
        MakeRecord(
            KeySet.Feature,
            MakeGroup(
                KJointFeature,
                ("rMatrix", None),
                ("sourceOccurrenceRef", LocalRef(SourceIds[0])),
            ),
            MakeGroup(KDcJointFeature, ("limits", ValueSeries(()))),
            MakeGroup(
                KConstraintFeature,
                ("operandOccRefs", LocalSeries((FirstIds[0], SecondIds[0]))),
                ("rAssyConstraint", LocalRef(JointId)),
            ),
            MakeGroup(KAssemblyFeature),
            *FeatureGroups("As-built", KeySet, RootInfo.ContextId, ()),
        ),
        *RefRecords(SideRef(RootInfo, First, FirstIds, KeySet.Feature, Alignment)),
        *RefRecords(SideRef(RootInfo, Second, SecondIds, KeySet.Feature, None)),
        *RefRecords(SourceRef(RootInfo, SourceIds, KeySet.Feature)),
        *ActionRecords(KeySet, RootInfo.NodesId),
        MakeRecord(
            DcOccurId,
            MakeGroup(
                KDcJointOccurrence,
                ("states", ValueSeries((FeatureState(KeySet.Feature),))),
            ),
            MakeGroup(
                KDcConstraintOcc,
                ("rAssyConstrFeature", LocalRef(KeySet.Feature)),
                ("rAssyConstrOccurrence", LocalRef(JointOccId)),
                ("rDcOccurrence", LocalRef(RootInfo.RootOccurrence)),
                ("stateIdx", 0),
            ),
        ),
        FrameRecord(
            JointOccId,
            EntityFrame("", (SubjectValue(LocalRef(JointId), 0),), None),
            MakeGroup(
                KJointOccurrence, ("dims", ValueSeries(())), ("m_state", JointState())
            ),
            MakeGroup(
                KConstraintOccurrence,
                ("creationIndex", 1),
                ("isVisible", True),
                ("pathToAssyConstr", OccurPath(RootInfo, ())),
                ("rAssyConstr", LocalRef(JointId)),
            ),
            MakeGroup(KCommonBase, ("rClientObject", None)),
            MakeGroup(KManagedEntity, ("rParent", LocalRef(RootInfo.ConstraintOccs))),
        ),
    )
