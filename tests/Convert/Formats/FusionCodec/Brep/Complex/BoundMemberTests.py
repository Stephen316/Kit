from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.Formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.Formats.Fusion.BrepCodec.Journal.JournalLimits import KBoardChanges
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeStateNode import (
    MakeStateNode,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KRecordTokens
from tests.Convert.Formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
)
from tests.Convert.Formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.Convert.Formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive

# study root needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KStudyRoot = "re/Fusion/Study/"

# the text case cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KTextCase = (
    KStudyRoot + "embosstext-cd769aa41cdf/two_texts.f3d",
    "9e5ddf77aed83af8e7f7cbadbd72e9e933823c7622320f28bbe1ab5f19df1b76",
)

# the largest case cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KLargestCase = (
    KStudyRoot + "rectsymholdouts-cf85ce4a0382/multiple_bodies.f3d",
    "80682e778a864030b4f03ba40ccaee4087d4a4d9c1376ec470d153b295325a82",
)

# the helix cases cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KHelixCases: tuple[tuple[str, str], ...] = (
    (
        KStudyRoot + "tappedholes-409e96788503/modeled_full.f3d",
        "2fbaa0edf5ab1dc002069e2c30bbfc0509fd4afd6e63adaa8c3b333dcb813f81",
    ),
    (
        KStudyRoot + "threadmodes-d51d2ae60564/modeled_full.f3d",
        "f7f4ccac9ac6696ed59707ccd97ff2a7b684906317fd61a408eed38445b00e3a",
    ),
)

# the wire cases cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KWireCases: tuple[tuple[str, str], ...] = (
    (
        KStudyRoot + "splitfacemodes-4fc4adf2a868/along_vector.f3d",
        "43b040d656315b71ab6e521a8d19231d243d78e7706668a974e107c8978e8ed1",
    ),
    (
        KStudyRoot + "splitfacemodes-4fc4adf2a868/closest_point.f3d",
        "2b6828acc2e271e82268dc60d4c7b084308ea65ed571f67f8829c3646dfe861a",
    ),
    (
        KStudyRoot + "surfacetrimtools-ca26d21e7ad9/sketch_line.f3d",
        "d05cd05813c03c1c1c72ac24795758f0288aed77b08197490312e93aa50d21e0",
    ),
    (
        KStudyRoot + "surfacetrimtools-650ca09579b1/sketch_line_offset_positive.f3d",
        "478847884f254534d632403ee0a0f66a161b23e6cd5e33bc1fe96287a2c061b2",
    ),
    (
        KStudyRoot + "surfacetrimtools-650ca09579b1/sketch_line_reversed_negative.f3d",
        "140509ba89f59477a4151badbe5d94351feff0137e68bbe88d9f3978d58a5b45",
    ),
)

# bound cases needs one explicit bound so native document reconstruction cannot accept inconsistent resource or layout limits
KBoundCases = (KTextCase, *KHelixCases, *KWireCases, KLargestCase)


# the bound bytes contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Digest", KBoundCases)
def TestBoundBytes(TmpPath: FilePath, Relative: str, Digest: str) -> None:
    Payload = ComplexMember(Relative, "smbh", Digest)
    Journal = ReadJournal(Payload)
    assert EmitJournal(Journal) == Payload
    assert JournalArchive(TmpPath / "BoundHistory.zip", Payload) == Journal


# the bound state contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Digest", KBoundCases)
def TestBoundState(TmpPath: FilePath, Relative: str, Digest: str) -> None:
    Journal = ReadJournal(ComplexMember(Relative, "smbh", Digest))
    Payload = EmitStateSmb(Journal)
    State = GeometryArchive(TmpPath / "BoundState.zip", Payload)
    assert EmitGeometry(State) == Payload
    assert len(State.Entities) == Journal.ActiveCount


# the large states contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "Relative,Digest,Tokens,Changes",
    ((*KLargestCase, 6687, 2224), (*KTextCase, 6636, 2207)),
)
def TestLargeStates(Relative: str, Digest: str, Tokens: int, Changes: int) -> None:
    Journal = ReadJournal(ComplexMember(Relative, "smbh", Digest))
    Largest = max(len(MakeStateNode(Value).Tokens) for Value in Journal.States)
    Widest = max(
        len(Board.Changes) for Value in Journal.States for Board in Value.Boards
    )
    assert (Largest, Widest) == (Tokens, Changes)
    assert 4096 < Largest <= KRecordTokens
    assert Widest <= KBoardChanges


# the record limit contract needs boundary coverage so stored document relationships remain consistent
def TestRecordLimit() -> None:
    Filled = AsmRecord("delta_state", ((4, 0),) * KRecordTokens)
    assert EmitWireRecord(Filled).endswith(b"\x11")
    Overfull = AsmRecord("delta_state", ((4, 0),) * (KRecordTokens + 1))
    with RaisesError(ValueError, match="Oversized Fusion journal wire record"):
        _ = EmitWireRecord(Overfull)


# the board limit contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestBoardLimit() -> None:
    Journal = ReadJournal(ComplexMember(KLargestCase[0], "smbh", KLargestCase[1]))

    # ordering by 0 boards couple 1 changes must stay deterministic so native document reconstruction resolves equivalent inputs consistently
    Place, BoardSpot = max(
        (
            (StateIndex, BoardIndex)
            for StateIndex, Value in enumerate(Journal.States)
            for BoardIndex in range(len(Value.Boards))
        ),
        key=lambda Couple: len(Journal.States[Couple[0]].Boards[Couple[1]].Changes),
    )
    State = Journal.States[Place]
    Board = State.Boards[BoardSpot]
    Padding = (Board.Changes[-1],) * (KBoardChanges + 1 - len(Board.Changes))
    Swollen = ReplaceValue(Board, Changes=Board.Changes + Padding)
    Boards = State.Boards[:BoardSpot] + (Swollen,) + State.Boards[BoardSpot + 1 :]
    States = list(Journal.States)
    States[Place] = ReplaceValue(State, Boards=Boards)
    with RaisesError(ValueError, match="Oversized Fusion bulletin change list"):
        _ = EmitJournal(ReplaceValue(Journal, States=tuple(States)))
