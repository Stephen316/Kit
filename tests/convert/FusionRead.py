from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.Fusion.Adapter import FusionReader
from convert.api.ApiContext import BuildRegistry
from interchange.document.models.DocumentModel import CadDocument


# research tests opt into incomplete fusion reads without changing the public registry
def OpenResearch(
    SourceData: KSourceType,
    *,
    SourceFormat: str | None = None,
    Configuration: str | None = None,
    IncludeBrep: bool = True,
    IncludeTess: bool = True,
    StrictMode: bool = True,
) -> CadDocument:
    Registry = BuildRegistry()
    Registry.register_reader(FusionReader())
    return Registry.read(
        SourceData,
        format_id=SourceFormat,
        options=ReadOptions(
            configuration=Configuration,
            include_brep=IncludeBrep,
            include_tessellation=IncludeTess,
            strict=StrictMode,
        ),
    )
