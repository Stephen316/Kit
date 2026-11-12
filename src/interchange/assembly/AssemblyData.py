from interchange.document.models.DocumentModel import (
    AssemblyData,
)

# historical import paths stay importable because pickles and adapters resolve assembly records here
__all__ = ("AssemblyData",)
