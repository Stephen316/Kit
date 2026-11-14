from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import approx as NearValue, mark as MarkTests

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from tests.convert.api.Fusion.Native.VendorCases import (
    KVendorCases,
    VendorCase,
    VendorSource,
)


@MarkTests.parametrize("CaseValue", KVendorCases)
def TestVendorRound(TmpPath: FilePath, CaseValue: VendorCase) -> None:
    Source = VendorSource(CaseValue)
    Document = OpenDocument(Source)
    assert tuple(Value.name for Value in Document.parameters) == CaseValue.Parameters
    assert Document.bodies[0].id == CaseValue.BodyId
    assert Document.bodies[0].topology.volume == NearValue(CaseValue.Volume)
    assert Document.materials[0].Density == CaseValue.Density
    assert len(Document.sketches[0].entities) == 9
    assert len(Document.feature_timeline) == 2
    assert not Document.brep_payloads and not Document.diagnostics
    Target = TmpPath / "Reemitted.f3d"
    Neutral = CadDocument.from_json(Document.to_json())
    assert Neutral == Document
    Result = WriteDocument(
        Neutral, Target, destination_format="f3d", allow_carrier=False
    )
    assert Result.application_usable and Result.vendor_loadable
    assert HashBytes(Target.read_bytes()).hexdigest() == CaseValue.OutputDigest
    assert ReadDocument(Target.read_bytes()) == ReadDocument(Source.read_bytes())
    Parsed = OpenDocument(Target)
    assert Parsed.parameters == Document.parameters
    assert Parsed.sketches == Document.sketches
    assert Parsed.brep == Document.brep
