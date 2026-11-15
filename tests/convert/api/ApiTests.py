from __future__ import annotations

from pathlib import Path as FilePath

import pytest as Pytest

from convert import ApplicationUsabilityError
from convert import available_adapters as GetAdapters
from convert import convert as ConvertLegacy
from convert import open_document as OpenLegacy
from convert import write_document as WriteLegacy
from convert.adapters import AdapterRegistry
from convert.adapters.base.AdapterProtocols import CadReaderAdapter, CadWriterAdapter
from interchange import Capability
from interchange.document.models.DocumentWalk import WalkDocuments
from interchange.features.FeatureKinds import NativeFeature
from tests.convert.api.ApiTestPaths import KCatPartPath
from tests.convert.api.ApiTestPaths import KFcstdPath
from tests.convert.api.BuildApiSource import BuildApiSource


# neutral interchange remains mandatory because independent adapters must never call each other
def CheckApiBridge(TmpPath: FilePath) -> None:
    FormatNames = {AdapterData.format_id for AdapterData in GetAdapters()}
    RegistryData = AdapterRegistry()
    _ = RegistryData.introspect()
    Adapters: tuple[CadReaderAdapter | CadWriterAdapter, ...] = (
        *RegistryData.readers(),
        *RegistryData.writers(),
    )
    assert FormatNames == {AdapterData.info.format_id for AdapterData in Adapters}
    SourcePath = BuildApiSource(TmpPath)
    DocumentData = OpenLegacy(SourcePath)
    OutputPath = TmpPath / "example.json"
    ResultData = ConvertLegacy(SourcePath, OutputPath)
    assert ResultData.source_format == "fusion.f3d"
    assert ResultData.destination_format == "interchange.json"
    assert ResultData.roundtrip_safe is True
    assert ResultData.near_lossless is True
    assert ResultData.dropped == frozenset()
    assert ResultData.requirements == ()
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.output.native_capabilities == frozenset(
        TransferData.capability for TransferData in ResultData.transfers
    )
    assert ResultData.output.carrier_capabilities == frozenset()
    assert OpenLegacy(OutputPath) == DocumentData


# legacy exact replay must still respect unresolved native history refusal
@Pytest.mark.parametrize(
    ("SourcePath", "FileName"),
    (
        (KFcstdPath, "exact.FCStd"),
        (KCatPartPath, "exact.CATPart"),
    ),
)
def CheckExactSwap(
    SourcePath: FilePath,
    FileName: str,
    TmpPath: FilePath,
) -> None:
    if not SourcePath.is_file():
        Pytest.skip(f"bundled exact replay fixture is unavailable: {SourcePath.name}")
    TargetPath = TmpPath / FileName
    DocumentData = OpenLegacy(SourcePath)
    if any(
        isinstance(StepValue.definition, NativeFeature)
        for PartValue in WalkDocuments(DocumentData)
        for StepValue in PartValue.feature_timeline
    ):
        _ = TargetPath.write_bytes(b"existing destination")
        with Pytest.raises(ValueError, match="native-only feature definitions"):
            _ = ConvertLegacy(SourcePath, TargetPath, overwrite=True)
        assert TargetPath.read_bytes() == b"existing destination"
        return
    ResultData = ConvertLegacy(SourcePath, TargetPath)
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.requirements == ()
    assert ResultData.dropped == frozenset()
    assert ResultData.output.native_capabilities
    assert ResultData.output.path == TargetPath.resolve()


# reversible carriers remain available because portable swaps must preserve unsupported semantics
def CheckCarryOut(TmpPath: FilePath) -> None:
    TargetPath = TmpPath / "portable.CATPart"
    ResultData = ConvertLegacy(BuildApiSource(TmpPath), TargetPath)
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert ResultData.near_lossless is False
    assert ResultData.roundtrip_safe is True
    assert ResultData.requirements == ()
    assert ResultData.dropped == frozenset()
    assert ResultData.output.carrier_capabilities
    assert TargetPath.is_file()


# strict mode must reject carrier output because callers explicitly require application usability
def CheckStrictGate(TmpPath: FilePath) -> None:
    SourcePath = BuildApiSource(TmpPath)
    TargetPath = TmpPath / "blocked.CATPart"
    with Pytest.raises(ApplicationUsabilityError) as CapturedError:
        _ = ConvertLegacy(SourcePath, TargetPath, allow_carrier=False)
    assert CapturedError.value.code == "output_not_application_usable"
    assert CapturedError.value.format_id == "catia.v5"
    assert "carrier_only" in CapturedError.value.issues
    assert not TargetPath.exists()
    assert tuple(TmpPath.iterdir()) == (SourcePath,)


# direct document writes need the same usability policy as one step conversions
def CheckWriteGate(TmpPath: FilePath) -> None:
    DocumentData = OpenLegacy(BuildApiSource(TmpPath))
    TargetPath = TmpPath / "portable.CATPart"
    ResultData = WriteLegacy(DocumentData, TargetPath)
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert ResultData.requirements == ()
    assert ResultData.dropped == frozenset()
    StrictPath = TmpPath / "blocked.CATPart"
    with Pytest.raises(ApplicationUsabilityError):
        _ = WriteLegacy(DocumentData, StrictPath, allow_carrier=False)
    assert not StrictPath.exists()


# carrier reporting must distinguish preserved opaque semantics from native target capabilities
def CheckCarryMode(TmpPath: FilePath) -> None:
    ResultData = ConvertLegacy(
        BuildApiSource(TmpPath),
        TmpPath / "example.CATPart",
        allow_carrier=True,
    )
    assert ResultData.roundtrip_safe is True
    assert ResultData.dropped == frozenset()
    assert ResultData.requirements == ()
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert ResultData.output.native_capabilities == frozenset()
    assert (
        ResultData.output.carrier_capabilities
        == ResultData.output.transferred_capabilities
    )


# tessellation selection stays public because callers may avoid large display payloads
def CheckTessellate() -> None:
    WithoutMesh = OpenLegacy(
        KCatPartPath,
        include_brep=False,
        include_tessellation=False,
    )
    WithMesh = OpenLegacy(
        KCatPartPath,
        include_brep=False,
        include_tessellation=True,
    )
    assert Capability.KTessellation not in WithoutMesh.Capabilities
    assert Capability.KTessellation in WithMesh.Capabilities
