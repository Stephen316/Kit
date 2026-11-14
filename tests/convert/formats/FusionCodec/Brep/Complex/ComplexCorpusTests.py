from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.ComplexEntity import (
    KComplexTypes,
)
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.PermuteJournal import PermuteJournal
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.PermuteGeometry import (
    PermuteGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Spline.CheckSubtypes import (
    CheckSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
    KComplexBounds,
    KComplexMembers,
)
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexOrders import (
    ShuffleOrder,
)
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive

KHistoryMembers = tuple(Value for Value in KComplexMembers if Value[1] == "smbh")
KBoundMembers = tuple(Value[:3] for Value in KComplexBounds)
KComplexNames = frozenset(
    (
        "spline-surface",
        "intcurve-curve",
        "pcurve",
        "tcoedge-coedge",
        "tedge-edge",
        "tvertex-vertex",
    )
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Suffix,Digest", KComplexMembers)
def TestMemberBytes(TmpPath: FilePath, Relative: str, Suffix: str, Digest: str) -> None:
    Payload = ComplexMember(Relative, Suffix, Digest)
    if Suffix == "smbh":
        Journal = ReadJournal(Payload)
        assert EmitJournal(Journal) == Payload
        assert JournalArchive(TmpPath / "ComplexHistory.zip", Payload) == Journal
        Entities = Journal.Entities
    else:
        Geometry = ReadGeometry(Payload)
        assert EmitGeometry(Geometry) == Payload
        assert GeometryArchive(TmpPath / "ComplexGeometry.zip", Payload) == Geometry
        Entities = Geometry.Entities
    assert any(isinstance(Value, KComplexTypes) for Value in Entities)
    CheckSubtypes(Entities)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Suffix,Digest", KComplexMembers)
def TestMemberOrder(Relative: str, Suffix: str, Digest: str) -> None:
    Payload = ComplexMember(Relative, Suffix, Digest)
    if Suffix == "smbh":
        Journal = ReadJournal(Payload)
        Moved = PermuteJournal(
            Journal, ShuffleOrder(Journal.Entities, Journal.ActiveCount, True)
        )
        Emitted = EmitJournal(Moved)
        assert ReadJournal(Emitted) == Moved
    else:
        Geometry = ReadGeometry(Payload)
        Shifted = PermuteGeometry(
            Geometry, ShuffleOrder(Geometry.Entities, len(Geometry.Entities), True)
        )
        Emitted = EmitGeometry(Shifted)
        assert ReadGeometry(Emitted) == Shifted
    assert Emitted != Payload


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Suffix,Digest", KHistoryMembers)
def TestForwardRefs(Relative: str, Suffix: str, Digest: str) -> None:
    Journal = ReadJournal(ComplexMember(Relative, Suffix, Digest))
    Order = ShuffleOrder(Journal.Entities, Journal.ActiveCount, False)
    with RaisesError(ValueError, match="subtype reference"):
        _ = EmitJournal(PermuteJournal(Journal, Order))


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Suffix,Digest", KHistoryMembers)
def TestMemberState(TmpPath: FilePath, Relative: str, Suffix: str, Digest: str) -> None:
    Journal = ReadJournal(ComplexMember(Relative, Suffix, Digest))
    Payload = EmitStateSmb(Journal)
    State = GeometryArchive(TmpPath / "ComplexState.zip", Payload)
    assert EmitGeometry(State) == Payload
    assert len(State.Entities) == Journal.ActiveCount
    LiveCount = sum(
        isinstance(Value, KComplexTypes)
        for Value in Journal.Entities[: Journal.ActiveCount]
    )
    assert LiveCount > 0
    assert sum(isinstance(Value, KComplexTypes) for Value in State.Entities) == (
        LiveCount
    )
    CheckSubtypes(State.Entities)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Suffix,Digest", KBoundMembers)
def TestMemberBound(Relative: str, Suffix: str, Digest: str) -> None:
    Payload = ComplexMember(Relative, Suffix, Digest)
    assert EmitJournal(ReadJournal(Payload)) == Payload


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Suffix,Digest", KBoundMembers)
def TestBoundNodes(Relative: str, Suffix: str, Digest: str) -> None:
    Table = ReadAsmTable(ComplexMember(Relative, Suffix, Digest))
    Records = tuple(Record for Record in Table.Records if Record.Name in KComplexNames)
    assert Records
    for Record in Records:
        Value = ReadEntityNode(Record)
        assert isinstance(Value, KComplexTypes)
        assert MakeEntityNode(Value) == Record
