from typing import Literal

from convert.adapters.Fusion import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from interchange import CadDocument

KProfileKind = Literal[
    "parameter", "circle", "rectangle", "extrusion", "cuboid", "frustum"
]
KProfileNames: tuple[KProfileKind, ...] = (
    "parameter",
    "circle",
    "rectangle",
    "extrusion",
    "cuboid",
    "frustum",
)


def AdapterCase(ProfileKind: KProfileKind) -> CadDocument:
    Specification = DocumentSpec(
        "Public Fusion",
        "publicHeight",
        17.0,
        ProfileKind,
        RadiusMm=12.0,
        WidthMm=19.0,
        DepthMm=23.0,
        Material=MaterialSpec(
            "Public Material", 2870.0, ColorValue(0.2, 0.4, 0.6, 1.0)
        ),
        TaperDegrees=5.0 if ProfileKind == "frustum" else 0.0,
        ConstrainRectangle=ProfileKind in ("rectangle", "cuboid"),
    )
    return MakeFusionDoc(Specification)
