from typing import Literal

from convert.adapters.Fusion import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from interchange import CadDocument

# the profile kind shape must stay shared so native document reconstruction uses one contract for compatible values
KProfileKind = Literal[
    "parameter", "circle", "rectangle", "extrusion", "cuboid", "frustum"
]

# the profile names cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KProfileNames: tuple[KProfileKind, ...] = (
    "parameter",
    "circle",
    "rectangle",
    "extrusion",
    "cuboid",
    "frustum",
)


# shared adapter case setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
