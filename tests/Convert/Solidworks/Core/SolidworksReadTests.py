from __future__ import annotations
from pathlib import Path as FilePath
import struct as StructLib
import pytest as PytestLib
from convert.adapters.solidworks import (
    SldprtArchive,
    SldprtFormatError,
    build_sldprt as BuildSldprt,
    decode_brep_model as DecodeBrepModel,
    encode_brep_model as EncodeBrepModel,
    read_sldprt as ReadSldprt,
)
from convert.adapters.solidworks.Container.Container import (
    container_signatures as ContainerSignatures,
)
from convert.adapters.solidworks.Container.Format import (
    PARTITION_STREAM as StreamI,
)
from convert.Geometry.Parasolid import (
    ParaHeaderData as ParasolidHeader,
    ScanPartRecords as ScanPartitionRecords,
)
from tests.Interchange.Brep.BrepTests import triangle_brep as TriangleBrep

# centralizes shared evidence so every related assertion uses one value
KSample = FilePath(__file__).parents[4] / "re" / "solidworks" / "examples" / ".SLDPRT" / "example.SLDPRT"

# centralizes shared evidence so every related assertion uses one value
KAssembly = (
    FilePath(__file__).parents[4] / "re" / "solidworks" / "examples" / "Random" / "Pistons" / "Piston.SLDASM"
)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPPDTKNB() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    Decoded = DecodeBrepModel(Encoded)
    assert Decoded is not None
    assert Decoded.GetErrors() == ()
    assert len(Decoded.bodies) == 1
    assert len(Decoded.faces) == 1
    assert len(Decoded.edges) == 3
    assert len(Decoded.vertices) == 3
    assert {Vertex.point for Vertex in Decoded.vertices} == {
        Vertex.point for Vertex in TriangleBrep().vertices
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def TestNSRPPAATB() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    SourceDoc = SldprtArchive.open(KSample)
    StreamsA = SourceDoc.streams
    StreamsA[StreamI] = Encoded
    _ = StreamsA.pop("Contents/Config-0-GhostPartition", None)
    Native = BuildSldprt(
        StreamsA,
        file_id=SourceDoc.file_id,
        format_version=SourceDoc.format_version,
        signatures=ContainerSignatures(KSample.read_bytes()),
    )
    Decoded = ReadSldprt(Native)
    assert Decoded.brep is not None
    assert Decoded.brep.GetErrors() == ()
    assert len(Decoded.brep_payloads) == 1
    assert Decoded.brep_payloads[0].data == Encoded


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPDROTAD() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    Broken = bytearray(Encoded)
    Header = ParasolidHeader(Encoded)
    assert Header is not None
    Tables = ScanPartitionRecords(Encoded[Header.body_offset :])
    assert Tables is not None
    LoopInfo = next(iter(Tables.loops.values()))
    StructLib.pack_into(">H", Broken, Header.body_offset + LoopInfo.offset + 10, 1)
    assert DecodeBrepModel(Broken) is None
    Deltas = Encoded.replace(b"partition", b"deltasxxx", 1)
    assert DecodeBrepModel(Deltas) is None


# keeps this focused behavior isolated so regressions remain immediately visible
def TestNSIBFOTARG() -> None:
    Encoded = EncodeBrepModel(TriangleBrep())
    SourceDoc = SldprtArchive.open(KSample)
    StreamsA = SourceDoc.streams
    StreamsA[StreamI] = Encoded
    _ = StreamsA.pop("Contents/Config-0-GhostPartition", None)
    Native = BuildSldprt(
        StreamsA,
        file_id=SourceDoc.file_id,
        format_version=SourceDoc.format_version,
        signatures=ContainerSignatures(KSample.read_bytes()),
    )
    Decoded = ReadSldprt(Native, include_brep=False)
    assert Decoded.brep is None
    assert Decoded.brep_payloads == ()


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    ("SourceDoc", "WrongSuffix"), ((KSample, ".SLDASM"), (KAssembly, ".SLDPRT"))
)
def TestSRRNSKM(SourceDoc: FilePath, WrongSuffix: str, TmpPath: FilePath) -> None:
    if not SourceDoc.is_file():
        PytestLib.skip("solidworks corpus unavailable")
    Renamed = TmpPath / f"renamed{WrongSuffix}"
    _ = Renamed.write_bytes(SourceDoc.read_bytes())
    with PytestLib.raises(SldprtFormatError, match="content requires"):
        _ = ReadSldprt(Renamed)
