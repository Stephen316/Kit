# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# only the verified native profile members can supply the bounded meridian
def ProfileLines(
    StepValue: FeatureStep, SketchValue: Sketch
) -> tuple[LineGeometry, ...]:
    Profile = ReadRevProfile(StepValue, SketchValue)
    if not isinstance(Profile, tuple) or len(Profile) != 4:
        raise ValueError("Fusion plane Revolve requires one four-line profile")
    return Profile


# ordered selection roles stay independent of the order of the geometric roots
def TargetPlanes(
    StepValue: FeatureStep,
    Picks: tuple[Selection, ...],
    Frames: dict[str, SupportPlane],
) -> tuple[tuple[Selection, SupportPlane], ...]:
    Ids = StepValue.attributes.get("fusion.revolve.target_selection_ids")
    if not isinstance(Ids, tuple) or len(Ids) not in (1, 2):
        raise ValueError("Fusion plane Revolve requires one or two targets")
    ById = {Value.id: Value for Value in Picks}
    Targets = []
    for RoleName, SelectId in zip(("target_one", "target_two"), Ids):
        PickValue = ById.get(f"fusion-selection-{SelectId}-{RoleName}")
        if PickValue is None or len(PickValue.path) != 1:
            raise ValueError("Missing Fusion plane Revolve target selection")
        (PathValue,) = PickValue.path
        FrameValue = Frames.get(PathValue.entity_id)
        if PathValue.entity_kind != "support_plane" or FrameValue is None:
            raise ValueError("Missing Fusion plane Revolve target frame")
        Targets.append((PickValue, FrameValue))
    return tuple(Targets)
