from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
)

KWireCases: tuple[tuple[str, str], ...] = (
    (
        "re/Fusion/Study/splitfacemodes-4fc4adf2a868/along_vector.f3d",
        "43b040d656315b71ab6e521a8d19231d243d78e7706668a974e107c8978e8ed1",
    ),
    (
        "re/Fusion/Study/splitfacemodes-4fc4adf2a868/closest_point.f3d",
        "2b6828acc2e271e82268dc60d4c7b084308ea65ed571f67f8829c3646dfe861a",
    ),
    (
        "re/Fusion/Study/surfacetrimtools-ca26d21e7ad9/sketch_line.f3d",
        "d05cd05813c03c1c1c72ac24795758f0288aed77b08197490312e93aa50d21e0",
    ),
    (
        "re/Fusion/Study/surfacetrimtools-650ca09579b1/sketch_line_offset_positive.f3d",
        "478847884f254534d632403ee0a0f66a161b23e6cd5e33bc1fe96287a2c061b2",
    ),
    (
        "re/Fusion/Study/surfacetrimtools-650ca09579b1/sketch_line_reversed_negative.f3d",
        "140509ba89f59477a4151badbe5d94351feff0137e68bbe88d9f3978d58a5b45",
    ),
)


def SwapEntity(
    Journal: JournalModel, Index: int, Value: KJournalEntity
) -> JournalModel:
    Entities = list(Journal.Entities)
    Entities[Index] = Value
    return ReplaceValue(Journal, Entities=tuple(Entities))


def FindWire(Journal: JournalModel) -> tuple[int, WireNode]:
    Found = tuple(
        (Index, Value)
        for Index, Value in enumerate(Journal.Entities)
        if isinstance(Value, WireNode)
    )
    assert len(Found) == 1
    return Found[0]


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Digest", KWireCases)
def TestWireRecord(Relative: str, Digest: str) -> None:
    Payload = ComplexMember(Relative, "smbh", Digest)
    Journal = ReadJournal(Payload)
    Index, Value = FindWire(Journal)
    assert Index < Journal.ActiveCount
    assert (Value.NextWire, Value.Inside) == (-1, False)
    Shell = Journal.Entities[Value.OwnerShell]
    assert isinstance(Shell, ShellNode)
    assert (Shell.FirstFace, Shell.FirstWire) == (-1, Index)
    Coedge = Journal.Entities[Value.FirstCoedge]
    assert isinstance(Coedge, CoedgeNode)
    assert Coedge.OwnerLoop == Index
    assert Coedge.NextCoedge == Coedge.PriorCoedge == Value.FirstCoedge
    assert Coedge.Partner == -1
    assert isinstance(Journal.Entities[Coedge.EdgeRef], EdgeNode)
    Record = MakeEntityNode(Value)
    assert Record.Name == "wire"
    assert Record.Tokens[6:] == ((12, -1), (11, None))
    assert ReadEntityNode(Record) == Value
    assert EmitJournal(Journal) == Payload


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Digest", KWireCases)
def TestWireFaults(Relative: str, Digest: str) -> None:
    Journal = ReadJournal(ComplexMember(Relative, "smbh", Digest))
    Index, Value = FindWire(Journal)
    Shell = Journal.Entities[Value.OwnerShell]
    assert isinstance(Shell, ShellNode)
    Unwired = SwapEntity(Journal, Value.OwnerShell, ReplaceValue(Shell, FirstWire=-1))
    with RaisesError(ValueError, match="Missing required Fusion topology reference"):
        _ = EmitJournal(Unwired)
    Orphan = SwapEntity(Journal, Index, ReplaceValue(Value, OwnerShell=-1))
    with RaisesError(ValueError, match="Missing required Fusion topology reference"):
        _ = EmitJournal(Orphan)
    Faces = (
        Position
        for Position, Other in enumerate(Journal.Entities[: Journal.ActiveCount])
        if isinstance(Other, FaceNode)
    )
    Misled = SwapEntity(Journal, Index, ReplaceValue(Value, FirstCoedge=next(Faces)))
    with RaisesError(ValueError, match="class-incompatible"):
        _ = EmitJournal(Misled)


def TestWireNode() -> None:
    for Inside in (False, True):
        Value = WireNode(EntityPrefix(-1, -1), -1, 15, 8, Inside)
        Record = MakeEntityNode(Value)
        Logic = (10, None) if Inside else (11, None)
        Heading = ((12, -1), (4, -1), (12, -1), (12, -1), (12, 15), (12, 8))
        assert Record == AsmRecord("wire", (*Heading, (12, -1), Logic))
        assert ReadEntityNode(Record) == Value
        with RaisesError(ValueError):
            _ = ReadEntityNode(AsmRecord("wire", (*Heading, (12, 4), Logic)))
