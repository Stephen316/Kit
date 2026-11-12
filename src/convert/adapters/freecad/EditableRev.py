from dataclasses import dataclass as MakeDataClass
from math import degrees as Degrees, tau as FullTurn

from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.adapters.freecad.EditRev.RevAxisProof import CheckRevAxis
from convert.adapters.freecad.EditRev.RevBodyProof import CheckRevBody
from convert.adapters.freecad.EditRev.RevProfileProof import CheckRevProfile
from convert.adapters.freecad.EditRev.RevScope import ReadRevScope
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Transform import KOriginZero
from interchange.geometry.models.VectorSpace import SpaceVector


# native controls preserve the signed sweep and any independently authored centered limits
@MakeDataClass(frozen=True, slots=True)
class EditRevolve:
    SketchId: str
    AxisOrigin: SpaceVector
    AxisDirection: SpaceVector
    AngleDeg: float
    AngleParamId: str
    AngleScale: float = 1.0
    Symmetric: bool = False
    AgainstParamId: str | None = None


# an exact reconstructed source body and origin axis qualify the native revolution
def ReadEditRevolve(
    DocValue: CadDocument, FeatureValue: FeatureStep
) -> EditRevolve | None:
    Definition = FeatureValue.definition
    if not isinstance(Definition, AngularRevolve):
        return None
    try:
        SketchValue, PlaneValue, BodyValue = ReadRevScope(DocValue, FeatureValue)
        CheckRevProfile(FeatureValue, SketchValue)
        CheckRevAxis(
            FeatureValue, Definition, DocValue.selections[0], PlaneValue.transform
        )
        Along, Against = ReadRevAngles(FeatureValue, Definition, DocValue.parameters)
        Interval = GetAngleSpan(Along, Against, Definition.SideMode)
        SpanValue = Interval[1] - Interval[0]
        IsCentered = Definition.SideMode != "one_sided"
        IsMirrored = Definition.SideMode == "symmetric"
        IsTwoSided = Definition.SideMode == "two_sided"
        if SpanValue > FullTurn or (
            IsTwoSided and Definition.AxisOrigin != KOriginZero
        ):
            return None
        CheckRevBody(
            BodyValue,
            DocValue,
            FeatureValue,
            Definition,
            Interval,
            SketchValue,
            PlaneValue,
        )
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None
    return EditRevolve(
        SketchValue.id,
        Definition.AxisOrigin,
        Definition.AxisDirection,
        Degrees(SpanValue if IsCentered else Along),
        Definition.AlongParameterId,
        2.0 if IsMirrored else 1.0,
        IsCentered,
        Definition.AgainstParameterId,
    )
