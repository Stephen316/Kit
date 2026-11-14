from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
    KFeatureLayouts,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
)

KThreadCases: tuple[tuple[str, str, int, int], ...] = (
    (
        "re/Fusion/Study/threadmodes-d51d2ae60564/modeled_full.f3d",
        "f7f4ccac9ac6696ed59707ccd97ff2a7b684906317fd61a408eed38445b00e3a",
        303,
        0,
    ),
    (
        "re/Fusion/Study/tappedholes-409e96788503/modeled_full.f3d",
        "2fbaa0edf5ab1dc002069e2c30bbfc0509fd4afd6e63adaa8c3b333dcb813f81",
        304,
        1,
    ),
)
KMergeCases: tuple[tuple[str, str], ...] = (
    (
        "re/Fusion/Study/splitfacemodes-4fc4adf2a868/along_vector.f3d",
        "43b040d656315b71ab6e521a8d19231d243d78e7706668a974e107c8978e8ed1",
    ),
    (
        "re/Fusion/Study/splitfacemodes-4fc4adf2a868/closest_point.f3d",
        "2b6828acc2e271e82268dc60d4c7b084308ea65ed571f67f8829c3646dfe861a",
    ),
)
KTypeCodes = {"feature_data": 1902, "thread_face_data": 1901}


def SwapEntity(
    Journal: JournalModel, Index: int, Value: KJournalEntity
) -> JournalModel:
    Entities = list(Journal.Entities)
    Entities[Index] = Value
    return ReplaceValue(Journal, Entities=tuple(Entities))


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Digest,FeatureTag,TailCode", KThreadCases)
def TestThreadData(Relative: str, Digest: str, FeatureTag: int, TailCode: int) -> None:
    Payload = ComplexMember(Relative, "smbh", Digest)
    Journal = ReadJournal(Payload)
    Values = tuple(
        Value for Value in Journal.Entities if isinstance(Value, FeatureAttrib)
    )
    assert {Value.DataName for Value in Values} == set(KFeatureLayouts)
    for Value in Values:
        assert isinstance(Journal.Entities[Value.Links.OwnerRef], FaceNode)
        assert (Value.FeatureTag, Value.Flags) == (FeatureTag, 2097152)
        assert Value.TypeCode == KTypeCodes[Value.DataName]
        Detailed = Value.DataName == "thread_face_data"
        assert len(Value.Points) == (3 if Detailed else 0)
        assert Value.TailCode == (TailCode if Detailed else None)
        assert all(IsFinite(Number) for Point in Value.Points for Number in Point)
        Record = MakeEntityNode(Value)
        assert Record.Tokens[5] == (7, "FDM_feature_attrib_def")
        assert ReadEntityNode(Record) == Value
    assert EmitJournal(Journal) == Payload


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestFdmFaults() -> None:
    Relative, Digest = KThreadCases[0][:2]
    Journal = ReadJournal(ComplexMember(Relative, "smbh", Digest))
    Values = tuple(
        Value for Value in Journal.Entities if isinstance(Value, FeatureAttrib)
    )
    Thread = next(Value for Value in Values if Value.DataName == "thread_face_data")
    Plain = next(Value for Value in Values if Value.DataName == "feature_data")
    Faults = (
        ReplaceValue(Thread, Points=()),
        ReplaceValue(Thread, TailCode=None),
        ReplaceValue(Plain, TailCode=0),
        ReplaceValue(Plain, Points=Thread.Points),
    )
    for Value in Faults:
        with RaisesError(ValueError, match="layout disagrees"):
            _ = MakeEntityNode(Value)
    with RaisesError(ValueError, match="Unsupported Fusion feature attribute data"):
        _ = MakeEntityNode(ReplaceValue(Plain, DataName="other_data"))
    Broken = ((float("nan"), 0.0, 0.0), *Thread.Points[1:])
    with RaisesError(ValueError, match="points must be finite"):
        _ = MakeEntityNode(ReplaceValue(Thread, Points=Broken))


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Digest", KMergeCases)
def TestNoMerge(Relative: str, Digest: str) -> None:
    Payload = ComplexMember(Relative, "smbh", Digest)
    Journal = ReadJournal(Payload)
    Found = tuple(
        (Index, Value)
        for Index, Value in enumerate(Journal.Entities)
        if isinstance(Value, NoMergeAttrib)
    )
    assert len(Found) == 1
    Index, Value = Found[0]
    assert Index < Journal.ActiveCount
    assert isinstance(Journal.Entities[Value.Links.OwnerRef], EdgeNode)
    Record = MakeEntityNode(Value)
    assert Record.Name == "no_merge_attribute-st-attrib"
    assert Record.Tokens[:2] == ((12, -1), (4, -1))
    assert len(Record.Tokens) == 5
    assert ReadEntityNode(Record) == Value
    assert EmitJournal(Journal) == Payload
    Faces = (
        Position
        for Position, Other in enumerate(Journal.Entities[: Journal.ActiveCount])
        if isinstance(Other, FaceNode)
    )
    Misowned = ReplaceValue(Value.Links, OwnerRef=next(Faces))
    with RaisesError(ValueError, match="class-incompatible"):
        _ = EmitJournal(SwapEntity(Journal, Index, ReplaceValue(Value, Links=Misowned)))


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestDegenerate() -> None:
    Relative, Digest = KThreadCases[1][:2]
    Journal = ReadJournal(ComplexMember(Relative, "smbh", Digest))
    Found = tuple(
        (Index, Value)
        for Index, Value in enumerate(Journal.Entities)
        if isinstance(Value, EdgeNode) and Value.CurveRef == -1
    )
    assert len(Found) == 2
    assert all(Value.StartVertex == Value.EndVertex for _, Value in Found)
    assert all((Value.StartParam, Value.EndParam) == (1.0, 0.0) for _, Value in Found)
    Index, Value = Found[0]
    assert Index < Journal.ActiveCount
    Elsewhere = next(
        Position
        for Position, Other in enumerate(Journal.Entities[: Journal.ActiveCount])
        if isinstance(Other, VertexNode) and Position != Value.StartVertex
    )
    Opened = ReplaceValue(Value, EndVertex=Elsewhere)
    with RaisesError(ValueError, match="Missing required Fusion topology reference"):
        _ = EmitJournal(SwapEntity(Journal, Index, Opened))
