# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditRing.RingInputs import ReadRingInput
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.Profiles.ProfileRef import KLoopGuid, KProfileGuid
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch


# the owned descriptor and loop identify every whole selected curve
def CheckRevMembers(FeatureValue: FeatureStep, SketchValue: Sketch) -> None:
    Attrs = FeatureValue.attributes
    Profile = Attrs.get("fusion.profile_entity_ids")
    Members = Attrs.get("fusion.profile_native_members")
    Directions = Attrs.get("fusion.profile_native_directions")
    Descriptor = Attrs.get("fusion.profile_descriptor_id")
    Origin = FeatureValue.provenance
    if (
        Origin is None
        or Origin.adapter != "fusion.f3d"
        or type(Descriptor) is not int
        or Descriptor <= 0
        or "fusion.profile_portions" in Attrs
        or not isinstance(Profile, tuple)
        or len(Profile) not in (3, 4)
        or any(not isinstance(Identity, str) for Identity in Profile)
        or len(set(Profile)) != len(Profile)
        or SketchValue.closed_profile_entity_ids != (Profile,)
        or not isinstance(Members, tuple)
        or len(Members) != len(Profile)
        or any(not isinstance(Identity, str) for Identity in Members)
        or set(Members) != set(Profile)
        or not isinstance(Directions, tuple)
        or len(Directions) != len(Profile)
        or any(type(Value) is not int or Value not in (0, 1) for Value in Directions)
    ):
        raise ValueError("FreeCAD editable Revolve profile membership is unresolved")
    Kinds = tuple(
        SpanValue.record_kind
        for SpanValue in Origin.spans
        if SpanValue.stream == KDesignPrefix + "BulkStream.dat"
        and SpanValue.offset >= 0
        and SpanValue.length > 0
    )
    if Kinds.count(KProfileGuid) != 1 or Kinds.count(KLoopGuid) != 1:
        raise ValueError("FreeCAD editable Revolve profile provenance is incomplete")


# shared endpoint identities qualify the default editable line ring
def CheckRevProfile(FeatureValue: FeatureStep, SketchValue: Sketch) -> None:
    CheckRevMembers(FeatureValue, SketchValue)
    ReadRingInput(SketchValue)
