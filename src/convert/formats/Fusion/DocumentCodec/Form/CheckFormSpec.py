from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFormBody import (
    CheckFormBody,
)
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Materials.CheckMaterial import CheckMaterial
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def CheckFormSpec(SpecValue: FormSpec) -> None:
    if not isinstance(CastValue(object, SpecValue), FormSpec):
        raise ValueError("A typed Fusion Form document specification is required")
    for TextValue in (SpecValue.Title, SpecValue.BodyName, SpecValue.FeatureName):
        if (
            not isinstance(CastValue(object, TextValue), str)
            or len(TextValue) > 1024
            or "\x00" in TextValue
        ):
            raise ValueError("Invalid Form document text")
    CheckMaterial(SpecValue.Material)
    CheckFormBody(SpecValue.Body, SpecValue.Surface)
    CheckSurface(SpecValue.Surface)
