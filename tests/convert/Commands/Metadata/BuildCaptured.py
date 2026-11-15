from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument


# textual replay metadata must remain distinguishable from independently qualified sketch geometry
def BuildCaptured() -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec(
            "Captured objects",
            "length",
            20.0,
            ProfileKind="rectangle",
            ConstrainRectangle=True,
        )
    )
    return ReplaceData(
        Document,
        metadata={
            **Document.metadata,
            "freecad": {
                "objects": [
                    {
                        "name": "CapturedFeature",
                        "type_id": "App::FeaturePython",
                        "order": 0,
                        "dependencies": [],
                        "properties": {
                            "Label": {
                                "tag": "Property",
                                "attributes": {
                                    "name": "Label",
                                    "type": "App::PropertyString",
                                },
                                "children": [
                                    {
                                        "tag": "String",
                                        "attributes": {"value": "captured text"},
                                        "children": [],
                                    }
                                ],
                            },
                        },
                    }
                ],
            },
        },
    )
