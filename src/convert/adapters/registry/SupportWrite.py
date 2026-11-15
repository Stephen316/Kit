from convert.adapters.solidworks.core.Native import KRefSupportSource
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments


def CheckSupports(Document: CadDocument) -> None:
    Findings = sorted(
        {
            f"{PartValue.source.path}: {Sketch.id}"
            for PartValue in WalkDocuments(Document)
            for Sketch in PartValue.sketches
            if (
                PartValue.source.format_id.casefold() == "solidworks.sldprt"
                or (
                    Sketch.provenance is not None
                    and Sketch.provenance.adapter.casefold() == "solidworks.sldprt"
                )
                or "support_plane_native_id" in Sketch.attributes
                or "support_plane_source" in Sketch.attributes
                or "unframed_support_plane_native_id" in Sketch.attributes
            )
            and (
                Sketch.attributes.get("support_plane_source") != KRefSupportSource
                or Sketch.attributes.get("unframed_support_plane_native_id") is not None
            )
        }
    )
    if Findings:
        raise ValueError(
            "unqualified SOLIDWORKS sketch support references: " + "; ".join(Findings)
        )
