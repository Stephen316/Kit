# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.adapters.freecad.EditRing.RingInputs import ReadRingInput
from convert.formats.Fusion.Profiles.ProfileRef import KLoopGuid, KProfileGuid
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch


# only native whole profile membership can identify an editable line ring
def HasRingBinding(FeatureValue: FeatureStep, SketchValue: Sketch) -> bool:
    Attributes = FeatureValue.attributes
    Profile = Attributes.get("fusion.profile_entity_ids")
    Members = Attributes.get("fusion.profile_native_members")
    Directions = Attributes.get("fusion.profile_native_directions")
    Descriptor = Attributes.get("fusion.profile_descriptor_id")
    Origin = FeatureValue.provenance
    if (
        FeatureValue.kind != FeatureKind.KExtrusion
        or FeatureValue.suppressed
        or FeatureValue.sketch_id != SketchValue.id
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or type(Descriptor) is not int
        or Descriptor <= 0
        or "fusion.profile_portions" in Attributes
        or not IsObjectTuple(Profile)
        or not 3 <= len(Profile) <= 64
        or any(not isinstance(Identity, str) for Identity in Profile)
        or SketchValue.closed_profile_entity_ids != (Profile,)
        or not IsObjectTuple(Members)
        or len(Members) != len(Profile)
        or any(not isinstance(Identity, str) for Identity in Members)
        or Members[0] != Profile[0]
        or set(Members) != set(Profile)
        or not IsObjectTuple(Directions)
        or len(Directions) != len(Profile)
        or any(
            type(Direction) is not int or Direction not in (0, 1)
            for Direction in Directions
        )
    ):
        return False
    RecordKinds = tuple(Value.record_kind for Value in Origin.spans)
    return RecordKinds.count(KProfileGuid) == RecordKinds.count(KLoopGuid) == 1


# build order remains exactly the order used by fusion source solid reconstruction
def GetEditRing(
    FeatureValue: FeatureStep, SketchValue: Sketch
) -> tuple[LineGeometry, ...] | None:
    if not HasRingBinding(FeatureValue, SketchValue):
        return None
    try:
        Profile, _ = ReadRingInput(SketchValue)
    except (ValueError, TypeError, OverflowError):
        return None
    return Profile


# only native points referenced by the selected ring may move with profile edits
def GetRingPoints(SketchValue: Sketch) -> frozenset[str] | None:
    try:
        _, PointIds = ReadRingInput(SketchValue)
    except (ValueError, TypeError, OverflowError):
        return None
    return PointIds
