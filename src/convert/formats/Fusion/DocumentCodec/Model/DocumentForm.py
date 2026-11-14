from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


@MakeDataClass(frozen=True, slots=True)
class DocumentForm:
    Name: str
    Surface: TsplineSurface
