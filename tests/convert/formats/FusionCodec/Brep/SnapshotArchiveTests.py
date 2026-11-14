from pathlib import Path as FilePath

from convert.formats.Fusion.BrepCodec.EmitSnapshot import EmitSnapshot
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import IsAsmFlag
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmVec
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Brep.CheckCircleSpan import CheckCircleSpan
from tests.convert.formats.FusionCodec.Brep.CheckTopology import CheckTopology
from tests.convert.formats.FusionCodec.Brep.ReadBodyFaces import ReadBodyFaces
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


def TestSnapshot(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    Target = TmpPath / "Snapshot.smb"
    Payload = EmitSnapshot(Sample.Model, Sample.TagSet, Sample.Stamp)
    assert Target.write_bytes(Payload) == len(Payload)
    Table = ReadAsmTable(Target.read_bytes())
    assert Table.RootCount == 4
    assert len(Table.Records) == 59
    assert all(ReadAsmInt(Record, 1) == -1 for Record in Table.Records[1:4])
    BodyFaces = tuple(ReadBodyFaces(Table, Identity) for Identity in range(1, 4))
    assert tuple(len(Faces) for Faces in BodyFaces) == (3, 1, 1)
    assert IsAsmFlag(BodyFaces[1][0], 9)
    assert not IsAsmFlag(BodyFaces[1][0], 10)
    assert not IsAsmFlag(BodyFaces[2][0], 9)
    assert len(BodyFaces[2][0].Tokens) == 10
    for Faces in BodyFaces[1:]:
        Plane = RequireAsm(Table, ReadAsmPtr(Faces[0], 7), "plane-surface", 11)
        Center = ReadAsmVec(Plane, 3, 19)
        assert (Center.x, Center.y, Center.z) == (0.3, -0.4, 0.5)
    CheckCircleSpan(Table, Sample.Model, 4)
    CheckTopology(Table)
