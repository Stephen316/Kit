from dataclasses import replace as Replace
from pathlib import Path as FilePath
from struct import pack as PackValue

from pytest import mark as TestMarks, raises as RaiseError

from convert.Formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.Formats.Fusion.BrepCodec.EmitSnapshot import EmitSnapshot
from convert.Formats.Fusion.BrepCodec.History.InsertState import MakeInsertState
from convert.Formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.Formats.Fusion.BrepCodec.ReadSnapshot import ReadSnapshot
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepRecord import EmitBrepRecord
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from tests.Convert.Formats.FusionCodec.Brep.SampleInputs import MakeSample


# the history bad contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.parametrize(
    "Mutation",
    (
        "version",
        "roots",
        "flags",
        "trailing",
        "truncated",
        "attribute",
        "replacement",
        "duplicate",
    ),
)
def TestHistoryBad(TmpPath: FilePath, Mutation: str) -> None:
    Sample = MakeSample()
    Payload = EmitHistory(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    if Mutation in ("version", "roots", "flags"):
        Offset, Number = {"version": (15, 23201), "roots": (31, 3), "flags": (39, 2)}[
            Mutation
        ]
        Payload = Payload[:Offset] + PackValue("<q", Number) + Payload[Offset + 8 :]
    elif Mutation == "trailing":
        Payload += b"uninterpreted"
    elif Mutation == "truncated":
        Payload = Payload[:-1]
    elif Mutation == "attribute":
        Payload = Payload.replace(
            b"generic_tag_attrib_def", b"unknown_tag_attrib_def", 1
        )
    else:
        Current = MakeInsertState(Sample.History, 35)
        Fields = list(Current.Fields)
        Fields[13 if Mutation == "replacement" else 14] = EntityRef(2)
        Changed = Replace(Current, Fields=tuple(Fields))
        Original = EmitBrepRecord(Current)
        assert Payload.count(Original) == 1
        Payload = Payload.replace(Original, EmitBrepRecord(Changed), 1)
    Target = TmpPath / "Rejected.smbh"
    _ = Target.write_bytes(Payload)
    with RaiseError(ValueError):
        _ = ReadHistory(Target.read_bytes())


# the snapshot history contract needs boundary coverage so stored document relationships remain consistent
def TestSnapHistory(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    Snapshot = EmitSnapshot(Sample.Model, Sample.TagSet, Sample.Stamp)
    History = EmitHistory(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    Target = TmpPath / "CrossProfile.bin"
    _ = Target.write_bytes(Snapshot)
    with RaiseError(ValueError, match="header profile"):
        _ = ReadHistory(Target.read_bytes())
    _ = Target.write_bytes(History)
    with RaiseError(ValueError, match="header profile"):
        _ = ReadSnapshot(Target.read_bytes())
    _ = Target.write_bytes(Snapshot + b"\0")
    with RaiseError(ValueError):
        _ = ReadSnapshot(Target.read_bytes())
