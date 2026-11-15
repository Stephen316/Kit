from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.DocumentCodec.Form.CheckTrimming import CheckTrimming
from convert.formats.Fusion.DocumentCodec.Form.IntegrationRules import KPowerMap
from convert.formats.Fusion.DocumentCodec.Form.SurfaceMass import SurfaceMass


def FormMass(Model: FormBody, IsClosed: bool) -> dict[str, float]:
    CheckTrimming(Model)
    Total = dict.fromkeys(("area", "volume", *KPowerMap), 0.0)
    for FaceValue in Model.Faces:
        for KeyValue, Value in SurfaceMass(FaceValue.Surface.Cache).items():
            Total[KeyValue] += Value
    if not IsClosed:
        for KeyValue in ("volume", *KPowerMap):
            Total[KeyValue] = 0.0
    if Total["volume"] < 0.0:
        for KeyValue in ("volume", *KPowerMap):
            Total[KeyValue] = -Total[KeyValue]
    return Total
