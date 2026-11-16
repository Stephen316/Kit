from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument


# geometry qualification must detect changed creator parameters paired with an old boundary representation
def BuildStale() -> CadDocument:
    Original = MakeFusionDoc(
        DocumentSpec(
            "Geometry contract",
            "height",
            20.0,
            ProfileKind="cuboid",
            ConstrainRectangle=True,
        )
    )
    Changed = MakeFusionDoc(
        DocumentSpec(
            "Geometry contract",
            "height",
            25.0,
            ProfileKind="cuboid",
            ConstrainRectangle=True,
        )
    )
    assert Original.brep is not None and Changed.brep is not None
    return ReplaceData(Changed, brep=Original.brep)
