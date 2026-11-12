from dataclasses import replace as Replace

from convert.adapters.freecad.EditRev.RebuildRevDoc import RebuildRevDoc
from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.adapters.freecad.EditRing.RingChange import CheckRingEdit
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Sketch import Sketch
from interchange.records.RecordParameter import Expression, Parameter


# keep original native ownership and literal spelling when a saved angle is unchanged
def SetRevAngle(Param: Parameter, Radians: float, SourceText: str) -> Parameter:
    if Param.value.value == Radians:
        return Param
    return Replace(
        Param,
        value=Replace(Param.value, value=Radians),
        expression=Expression(SourceText, language="freecad"),
    )


# one neutral rebuild keeps the edited controls and the original solid identity together
def ApplyRevEdit(
    DocValue: CadDocument,
    Profile: Sketch,
    Along: tuple[float, str],
    Against: tuple[float, str] | None,
) -> CadDocument:
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    if not isinstance(Definition, AngularRevolve):
        raise ValueError("FreeCAD editable Revolve source definition is unavailable")
    if (Definition.AgainstParameterId is None) != (Against is None):
        raise ValueError("FreeCAD editable Revolve against angle binding changed")
    AngleEdits = {Definition.AlongParameterId: Along}
    if Definition.AgainstParameterId is not None and Against is not None:
        AngleEdits[Definition.AgainstParameterId] = Against
    Parameters = tuple(
        SetRevAngle(Value, *AngleEdits[Value.id]) for Value in DocValue.parameters
    )
    (Original,) = DocValue.sketches
    if Profile == Original and Parameters == DocValue.parameters:
        return DocValue
    if Profile != Original:
        CheckRingEdit(Original, Profile)
    AlongValue, AgainstValue = ReadRevAngles(Feature, Definition, Parameters)
    SpanValue = GetAngleSpan(AlongValue, AgainstValue, Definition.SideMode)
    (PlaneValue,) = DocValue.support_planes
    return RebuildRevDoc(
        Replace(DocValue, parameters=Parameters),
        Profile,
        PlaneValue.transform,
        SpanValue,
    )
