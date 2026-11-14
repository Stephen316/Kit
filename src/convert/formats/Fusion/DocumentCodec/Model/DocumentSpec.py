from dataclasses import dataclass as MakeDataClass
from typing import Literal

from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)


@MakeDataClass(frozen=True, slots=True)
class DocumentSpec:
    Title: str
    ParamName: str
    LengthMm: float
    ProfileKind: Literal[
        "parameter",
        "circle",
        "extrusion",
        "rectangle",
        "cuboid",
        "frustum",
        "part",
        "form",
    ] = "extrusion"
    RadiusMm: float = 12.5
    ParamComment: str = ""
    SketchName: str = "Authored Circle"
    ExtrusionName: str = "Authored Extrusion"
    BodyName: str = "Authored Cylinder"
    WidthMm: float = 40.0
    DepthMm: float = 30.0
    Material: MaterialSpec = MaterialSpec()
    TaperDegrees: float = 0.0
    ConstrainRectangle: bool = False
    WidthParamName: str = "rectangleWidth"
    DepthParamName: str = "rectangleDepth"
    Features: tuple[KPartFeature, ...] = ()
