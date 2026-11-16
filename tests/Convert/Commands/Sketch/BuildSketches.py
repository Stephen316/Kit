from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch, SketchEntity


# incomplete sketch histories need valid geometry so refusal exercises the intended conversion boundary
def BuildSketches(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec("Sketch history", "radius", 20.0, ProfileKind="circle")
    )
    if RecordKind == "Empty":
        return ReplaceData(Document, feature_timeline=(), metadata={})
    OtherSketch = Sketch(
        "sketch:other",
        "Other sketch",
        Document.sketches[0].support_plane_id,
        (
            SketchEntity(
                "entity:other", "circle", Document.sketches[0].entities[0].geometry
            ),
        ),
        closed_profile_entity_ids=(("entity:other",),),
    )
    Features = Document.feature_timeline
    if RecordKind == "Unrelated":
        Features = (ReplaceData(Features[0], sketch_id=OtherSketch.id),)
    return ReplaceData(
        Document,
        sketches=(*Document.sketches, OtherSketch),
        feature_timeline=Features,
        metadata={},
    )
