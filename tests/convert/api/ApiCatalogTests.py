from inspect import isabstract as IsAbstract
from typing import cast

import pytest as Pytest

from convert import available_adapters as GetAdapters
from convert.adapters import AdapterInfo, AdapterNotFoundError, AdapterRegistry
from convert.adapters.base.AdapterProtocols import CadReaderAdapter, CadWriterAdapter
from interchange import Capability
from tests.convert.api.ApiTestHelpers import GetPackNames, ListFormatPacks
from tests.convert.api.CatalogAliases import AssertAliases

# existing bidirectional formats retain their established reader and writer capabilities
KLegacyFormats = frozenset(
    {"catia.v5", "freecad.fcstd", "interchange.json", "solidworks.sldprt"}
)


# deterministic introspection prevents import order from changing the public format catalog
def CheckDiscovery() -> None:
    PackageNames = ListFormatPacks()
    FirstRegistry = AdapterRegistry()
    FirstIds = FirstRegistry.introspect()
    SecondRegistry = AdapterRegistry()
    SecondIds = SecondRegistry.introspect()
    ReaderValues = FirstRegistry.readers()
    WriterValues = FirstRegistry.writers()
    assert PackageNames
    assert GetPackNames((*ReaderValues, *WriterValues), PackageNames) == set(
        PackageNames
    )
    ReaderIds = tuple(ValueData.info.format_id for ValueData in ReaderValues)
    WriterIds = tuple(ValueData.info.format_id for ValueData in WriterValues)
    assert ReaderIds == tuple(sorted(set(ReaderIds)))
    assert WriterIds == tuple(sorted(set(WriterIds)))
    assert FirstIds == SecondIds == tuple(sorted(set(ReaderIds) | set(WriterIds)))
    assert KLegacyFormats <= set(ReaderIds) & set(WriterIds)
    assert "fusion.f3d" not in ReaderIds
    for FormatId in ("f3d", "fusion.f3d"):
        with Pytest.raises(AdapterNotFoundError):
            _ = FirstRegistry.reader(FormatId)
    assert "fusion.f3d" not in WriterIds
    AssertAliases(FirstRegistry)
    assert FirstRegistry.introspect() == FirstIds
    assert FirstRegistry.readers() == ReaderValues
    assert FirstRegistry.writers() == WriterValues
    assert all(
        not IsAbstract(type(AdapterData))
        and not getattr(type(AdapterData), "_is_protocol", False)
        for AdapterData in (*ReaderValues, *WriterValues)
    )
    AssertCaps((*ReaderValues, *WriterValues))


# the registry advertises capabilities consistently across discovered adapter families
def AssertCaps(
    Adapters: tuple[CadReaderAdapter | CadWriterAdapter, ...],
) -> None:
    assert all(
        AdapterData.info.capabilities == frozenset(Capability)
        for AdapterData in Adapters
        if AdapterData.info.format_id in KLegacyFormats
    )


# document kind extensions remain introspective so clients need no format specific branches
def CheckDocExts() -> None:
    AdapterMap = {InfoData.format_id: InfoData for InfoData in GetAdapters()}
    assert AdapterMap["solidworks.sldprt"].part_extensions == (".sldprt",)
    assert AdapterMap["solidworks.sldprt"].assembly_extensions == (".sldasm",)
    assert AdapterMap["catia.v5"].part_extensions == (".catpart",)
    assert AdapterMap["catia.v5"].assembly_extensions == (".catproduct",)
    assert AdapterMap["freecad.fcstd"].part_extensions == (".FCStd",)
    assert AdapterMap["freecad.fcstd"].assembly_extensions == (".FCStd",)
    for InfoData in AdapterMap.values():
        assert set(InfoData.extensions_for(assembly=False)) <= set(InfoData.extensions)
        assert set(InfoData.extensions_for(assembly=True)) <= set(InfoData.extensions)
    with Pytest.raises(TypeError):
        _ = AdapterMap["freecad.fcstd"].extensions_for(assembly=cast(bool, 1))
    AssemblyInfo = AdapterInfo(
        "format.assembly-only",
        "Assembly only",
        "1",
        (".assembly",),
        assembly_extensions=(".assembly",),
    )
    assert AssemblyInfo.extensions_for(assembly=False) == ()
    assert AssemblyInfo.extensions_for(assembly=True) == (".assembly",)
