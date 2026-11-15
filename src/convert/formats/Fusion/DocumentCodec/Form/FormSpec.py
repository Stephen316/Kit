from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


# form specification needs an explicit state contract so editable control cages retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class FormSpec:
    Title: str
    Surface: TsplineSurface
    Body: FormBody
    BodyName: str = ""
    FeatureName: str = ""
    Material: MaterialSpec = MaterialSpec()
