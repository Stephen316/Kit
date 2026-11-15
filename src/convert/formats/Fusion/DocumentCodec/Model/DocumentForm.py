from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


# document form needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class DocumentForm:
    Name: str
    Surface: TsplineSurface
