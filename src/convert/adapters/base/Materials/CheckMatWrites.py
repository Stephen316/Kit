from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.Materials.MaterialWriter import MaterialWriter
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments


def CheckMatWrites(Document: CadDocument, Adapter: CadWriterAdapter) -> None:
    if not any(Value.materials for Value in WalkDocuments(Document)):
        return
    if not isinstance(Adapter, MaterialWriter) or Adapter.TypedMaterials is not True:
        raise ValueError(
            f"{Adapter.info.format_id} does not support typed material density and color"
        )
