from pathlib import Path as FilePath

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmNum
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmText
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Brep.CheckCircleSpan import CheckCircleSpan
from tests.convert.formats.FusionCodec.Brep.CheckTopology import CheckTopology
from tests.convert.formats.FusionCodec.Brep.ReadBodyFaces import ReadBodyFaces
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


def TestHistory(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    Target = TmpPath / "History.smbh"
    Payload = EmitHistory(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    assert Target.write_bytes(Payload) == len(Payload)
    Table = ReadAsmTable(Target.read_bytes())
    assert Table.RootCount == 2
    assert len(Table.Records) == 35
    BodyRoot = RequireAsm(Table, 1, "body", 6)
    assert ReadAsmInt(BodyRoot, 1) == Sample.Identity.BodyKey
    TimestampId = ReadAsmPtr(BodyRoot, 0)
    Timestamp = RequireAsm(Table, TimestampId, "ATTRIB_CUSTOM-attrib", 8)
    assert ReadAsmText(Timestamp, 5) == "Timestamp_attrib_def"
    assert ReadAsmNum(Timestamp, 7) == Sample.Identity.AuthoredMicros
    Generic = RequireAsm(Table, ReadAsmPtr(Timestamp, 2), "ATTRIB_CUSTOM-attrib", 16)
    assert ReadAsmPtr(Generic, 3) == TimestampId
    assert ReadAsmPtr(Generic, 4) == 1
    assert ReadAsmText(Generic, 12) == str(Sample.Identity.OperationId)
    assert ReadAsmInt(Generic, 11) == len(
        str(Sample.Identity.OperationId).encode("ascii")
    )
    assert ReadAsmInt(Generic, 13) == Sample.Identity.SecondaryId
    assert ReadAsmInt(Generic, 13) != Sample.History.CurrentId
    assert len(ReadBodyFaces(Table, 1)) == 3
    CheckCircleSpan(Table, Sample.Model, 2)
    CheckTopology(Table)
