from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Projection.ProjectNative import ProjectNative
from convert.adapters.Fusion.Native.Projection.ProjectVendor import ProjectVendor
from convert.adapters.Fusion.Bridge.NativeVersion import NativeVersion
from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.document.Models.DocumentModel import CadDocument


# the document operation needs a consistent construction rule so public document claims remain grounded in native records
def EncodeDocument(Document: CadDocument) -> bytes:
    Document.AssertValid()
    if set(Document.metadata) == {"fusion.authoring"}:
        SpecValue = CheckContract(Document.metadata["fusion.authoring"], "spec")
        if (
            not isinstance(SpecValue, DocumentSpec)
            or MakeFusionDoc(SpecValue) != Document
        ):
            raise ValueError("Fusion authoring contract and neutral graph disagree")
        return EmitDocument(SpecValue)
    if set(Document.metadata) != {"fusion.native_state"}:
        raise ValueError(
            "Fusion writing requires a qualified authoring or native-state contract"
        )
    Version = NativeVersion(Document.metadata["fusion.native_state"])
    ModelValue = CheckContract(
        Document.metadata["fusion.native_state"], "model", Version
    )
    if not isinstance(ModelValue, DocumentModel):
        raise ValueError("Fusion native-state contract requires a document model")
    if Version == 1 and (
        ModelValue.Graphics is not None
        or ModelValue.Snapshots
        or ModelValue.Configurations
    ):
        raise ValueError("Native-state version 1 requires the authored profile")
    Payload = EmitParsed(ModelValue)
    Decoded = ReadDocument(Payload)
    Projector = ProjectVendor if Version == 2 else ProjectNative
    Projected = ReplaceData(
        Projector(Decoded, Document.source), metadata=Document.metadata
    )
    if Decoded != ModelValue or ModelValue.Meshes or Projected != Document:
        raise ValueError("Fusion native-state contract and neutral graph disagree")
    return Payload
