from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument


# sketch qualification needs valid reference histories independent of dimension and contract evidence
def BuildSketchDims(RecordKind: str) -> CadDocument:
    SpecValue = DocumentSpec(
        "Sketch dimensions",
        "length",
        20.0,
        ProfileKind=(
            "extrusion"
            if RecordKind == "Cylinder"
            else (
                "cuboid"
                if RecordKind == "Cuboid"
                else "circle" if RecordKind == "Circle" else "rectangle"
            )
        ),
        ConstrainRectangle=RecordKind
        not in ("Circle", "Rectangle", "Cylinder", "Cuboid"),
    )
    Document = MakeFusionDoc(SpecValue)
    if RecordKind == "NoContract":
        return ReplaceData(Document, metadata={})
    if RecordKind == "Stale":
        Changed = MakeFusionDoc(ReplaceData(SpecValue, WidthMm=SpecValue.WidthMm + 5.0))
        return ReplaceData(Document, sketches=Changed.sketches)
    if RecordKind in ("Suppressed", "Reference"):
        Sketch = Document.sketches[0]
        return ReplaceData(
            Document,
            sketches=(
                ReplaceData(
                    Sketch,
                    constraints=tuple(
                        (
                            ReplaceData(
                                Relation,
                                suppressed=RecordKind == "Suppressed",
                                driving=RecordKind != "Reference",
                            )
                            if Relation.parameter_id
                            else Relation
                        )
                        for Relation in Sketch.constraints
                    ),
                ),
            ),
        )
    return Document
