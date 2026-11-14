from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.SnapshotForm import SnapshotForm
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
    KComplexMembers,
)
from tests.convert.formats.FusionCodec.Brep.Complex.SnapshotStates import (
    KSnapshotStates,
)

KAuthoredRoot = (
    FilePath(__file__).resolve().parents[6] / "re/Fusion/LocalOracle/ComplexGeometry"
)
KAuthoredNames = ("AuthoredPatch", "AuthoredRational", "AuthoredPillow")
KHistoryMembers = tuple(Value for Value in KComplexMembers if Value[1] == "smbh")


def IsSnapshotStyle(Entities: tuple[KJournalEntity, ...]) -> bool:
    TagValues = {MakeEntityNode(Value).Tokens[1][1] for Value in Entities}
    Owned = any(
        isinstance(Value, (TimeAttrib, TagAttrib))
        and isinstance(Entities[Value.Links.OwnerRef], BodyNode)
        for Value in Entities
    )
    Tracked = any(isinstance(Value, TrackAttrib) for Value in Entities)
    return TagValues == {-1} and not Owned and not Tracked


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,HistoryDigest,SnapshotDigest,StateId", KSnapshotStates)
def TestFormBytes(
    Relative: str, HistoryDigest: str, SnapshotDigest: str, StateId: int
) -> None:
    Journal = ReadJournal(ComplexMember(Relative, "smbh", HistoryDigest))
    Payload = ComplexMember(Relative, "smb", SnapshotDigest)
    assert EmitStateSmb(Journal, StateId, Snapshot=True) == Payload
    assert EmitStateSmb(Journal, StateId) != Payload
    Entities = ReadGeometry(Payload).Entities
    assert SnapshotForm(Entities) == Entities


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Relative,Suffix,Digest", KHistoryMembers)
def TestFormHistory(Relative: str, Suffix: str, Digest: str) -> None:
    Journal = ReadJournal(ComplexMember(Relative, Suffix, Digest))
    Plain = ReadGeometry(EmitStateSmb(Journal)).Entities
    Entities = ReadGeometry(EmitStateSmb(Journal, Snapshot=True)).Entities
    assert IsSnapshotStyle(Entities)
    assert SnapshotForm(Entities) == Entities
    assert sum(isinstance(Value, BodyNode) for Value in Entities) == sum(
        isinstance(Value, BodyNode) for Value in Plain
    )


@TestMarks.parametrize("Label", KAuthoredNames)
def TestFormAuthor(Label: str) -> None:
    Journal = ReadJournal((KAuthoredRoot / (Label + ".smbh")).read_bytes())
    Stored = (KAuthoredRoot / (Label + ".smb")).read_bytes()
    assert EmitStateSmb(Journal) == Stored
    Entities = ReadGeometry(EmitStateSmb(Journal, Snapshot=True)).Entities
    assert IsSnapshotStyle(Entities)
    assert SnapshotForm(Entities) == Entities
    assert len(Entities) == len(ReadGeometry(Stored).Entities)


def TestFormFaults() -> None:
    Journal = ReadJournal((KAuthoredRoot / "AuthoredPatch.smbh").read_bytes())
    Entities = ReadGeometry((KAuthoredRoot / "AuthoredPatch.smb").read_bytes()).Entities
    Leader = Entities[0]
    assert isinstance(Leader, AsmRoot)
    Orphan = PointNode(EntityPrefix(-1, -1), (0.0, 0.0, 0.0))
    with RaisesError(ValueError, match="leading ASM header"):
        _ = SnapshotForm(Entities[1:])
    with RaisesError(ValueError, match="leading ASM header"):
        _ = SnapshotForm((ReplaceValue(Leader, Attribute=1), *Entities[1:]))
    with RaisesError(ValueError, match="unreachable record"):
        _ = SnapshotForm((*Entities, Orphan))
    with RaisesError(ValueError, match="boolean"):
        _ = EmitStateSmb(Journal, Snapshot=CastValue(bool, 1))
