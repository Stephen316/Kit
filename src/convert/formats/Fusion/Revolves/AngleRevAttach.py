# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.AngularAxis import ResolveAngleAxis
from convert.formats.Fusion.Revolves.AngleRevValues import ReadAngleSpan
from convert.formats.Fusion.Revolves.MeridianSense import ChooseMeridian
from convert.formats.Fusion.Revolves.ProfileMeridian import CalcMeridian
from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter


# an editable angular sweep must bind its signed limits and qualified source axis
def AttachAngleRev(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Picks: tuple[Selection, ...],
    Frames: dict[str, SupportPlane],
    Sketches: dict[str, Sketch],
    Params: dict[str, Parameter],
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
    AxisPick, Origin, StoredAxis = ResolveAngleAxis(
        BulkData, Owners, StepValue, Picks, Sketches, Frames, ProfileFrame
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
    else:
        EffectiveAxis, _ = CalcMeridian(
            ProfileFrame.transform, Profile, Origin, StoredAxis
        )
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
        AxisDirection=SpaceVector(*EffectiveAxis),
        SideMode=SideMode,
    )
    ReadAngleSpan(Definition, Params)
    return (
        Replace(
            StepValue,
            operation=BooleanOp.KCreate,
            definition=Definition,
            selection_ids=tuple(dict.fromkeys((AxisPick.id, *StepValue.selection_ids))),
        ),
        AxisPick,
    )
