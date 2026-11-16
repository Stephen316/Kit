from collections.abc import Callable
from dataclasses import replace as Replace
from math import isclose as IsClose, tau as FullTurn

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.AngularAxis import ReadAngleAxis
from convert.Formats.Fusion.Revolves.AngleRevValues import ReadAngleSpan
from convert.Formats.Fusion.Revolves.MeridianSense import ChooseMeridian
from convert.Formats.Fusion.Revolves.ProfileMeridian import CalcMeridian
from convert.Formats.Fusion.Revolves.RevProfile import ReadRevProfile
from convert.Formats.Fusion.Revolves.SphereMeridian import ReadSphereAxis
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter


# an editable angular sweep must bind its signed limits and qualified source axis
def AttachAngleRev(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Picks: tuple[Selection, ...],
    Frames: dict[str, SupportPlane],
    Sketches: dict[str, Sketch],
    Params: dict[str, Parameter],
    LoadEdge: Callable[[], tuple[Selection, SpaceVector, SpaceVector]] | None = None,
) -> tuple[FeatureStep, Selection]:
    Attrs = StepValue.attributes
    if (
        Attrs.get("fusion.revolve.operation") != "new_body"
        or Attrs.get("fusion.revolve.solid") is not True
        or Attrs.get("fusion.revolve.project_axis") is not False
    ):
        raise ValueError(
            "Fusion angular Revolve requires an unprojected solid new body"
        )
    SketchValue = Sketches.get(StepValue.sketch_id or "")
    ProfileFrame = (
        None if SketchValue is None else Frames.get(SketchValue.support_plane_id)
    )
    if SketchValue is None or ProfileFrame is None:
        raise ValueError("Missing Fusion angular Revolve profile sketch frame")
    AxisPick, Origin, StoredAxis = (
        ReadAngleAxis(
            BulkData, Owners, StepValue, Picks, Sketches, Frames, ProfileFrame
        )
        if LoadEdge is None
        else LoadEdge()
    )
    Profile = ReadRevProfile(StepValue, SketchValue)
    if isinstance(Profile, CircleGeometry):
        EffectiveAxis, _ = ChooseMeridian(
            ProfileFrame.transform,
            (Profile.center,),
            Origin,
            StoredAxis,
            Profile.radius,
        )
        Direction = SpaceVector(*EffectiveAxis)
    elif isinstance(Profile, ArcGeometry):
        _, Direction, _ = ReadSphereAxis(
            ProfileFrame.transform, Profile, Origin, StoredAxis
        )
    else:
        EffectiveAxis, _ = CalcMeridian(
            ProfileFrame.transform, Profile, Origin, StoredAxis
        )
        Direction = SpaceVector(*EffectiveAxis)
    AlongId = Attrs.get("fusion.revolve.along_parameter_id")
    AgainstId = Attrs.get("fusion.revolve.against_parameter_id")
    SideMode = Attrs.get("fusion.revolve.sidedness")
    if (
        not isinstance(AlongId, str)
        or not isinstance(SideMode, str)
        or (AgainstId is not None and not isinstance(AgainstId, str))
    ):
        raise ValueError("Missing Fusion angular Revolve limit bindings")
    Definition = AngularRevolve(
        AxisSelectionId=AxisPick.id,
        AlongParameterId=AlongId,
        AgainstParameterId=AgainstId,
        AxisOrigin=Origin,
        AxisDirection=Direction,
        SideMode=SideMode,
    )
    Start, EndValue = ReadAngleSpan(Definition, Params)
    if isinstance(Profile, ArcGeometry) and not IsClose(
        EndValue - Start, FullTurn, rel_tol=0.0, abs_tol=1e-10
    ):
        raise ValueError("Fusion semicircle Revolve requires one full turn")
    return (
        Replace(
            StepValue,
            operation=BooleanOp.KCreate,
            definition=Definition,
            selection_ids=tuple(dict.fromkeys((AxisPick.id, *StepValue.selection_ids))),
        ),
        AxisPick,
    )
