from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration


# configuration transfer coverage needs a real document that exposes target carrier fallback
def BuildVariants() -> CadDocument:
    return ReplaceData(
        MakeFusionDoc(
            DocumentSpec(
                "Configuration policy", "height", 20.0, ProfileKind="parameter"
            )
        ),
        configurations=(
            Configuration("config:first", "First", active=True),
            Configuration("config:second", "Second"),
        ),
        metadata={},
    )
