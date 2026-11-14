from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert import registry as RegistryValue
from interchange import CadDocument, Capability
from tests.convert.api.Fusion.AdapterCases import (
    AdapterCase,
    KProfileKind,
    KProfileNames,
)


@MarkTests.parametrize("ProfileKind", KProfileNames)
def TestPublicRound(TmpPath: FilePath, ProfileKind: KProfileKind) -> None:
    Document = AdapterCase(ProfileKind)
    Serialized = CadDocument.from_json(Document.to_json())
    assert Serialized == Document
    assert Serialized.Source == Document.source
    assert Serialized.Parameters == Document.parameters
    assert Serialized.BrepModel == Document.brep
    Source = TmpPath / "Authored.f3d"
    Result = WriteDocument(
        Serialized, Source, destination_format="f3d", allow_carrier=False
    )
    assert Result.application_usable and Result.vendor_loadable
    assert not Result.carrier_capabilities and not Result.dropped
    Parsed = OpenDocument(Source)
    assert not Parsed.brep_payloads and not Parsed.diagnostics
    assert Parsed.parameters[0].value.value == 17.0
    assert len(Parsed.feature_timeline) == len(Document.feature_timeline)
    assert Parsed.sketches == Document.sketches
    if Document.bodies:
        assert Parsed.brep == Document.brep
        assert Parsed.materials == Document.materials
        assert Capability.KMaterials in Result.native_capabilities
    Target = TmpPath / "Reemitted.f3d"
    _ = WriteDocument(
        CadDocument.from_json(Parsed.to_json()),
        Target,
        destination_format="fusion.f3d",
        allow_carrier=False,
    )
    assert Target.read_bytes() == Source.read_bytes()
    assert RegistryValue.GetReader("f3d").info == RegistryValue.GetWriter("f3d").info
