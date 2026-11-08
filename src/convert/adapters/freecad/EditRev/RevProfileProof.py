# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditExtProfile import GetCenterPoint
from convert.adapters.freecad.EditRing.RingInputs import ReadRingInput
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.Profiles.ProfileRef import KLoopGuid, KProfileGuid
from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import Sketch


# reciprocal descriptor and loop evidence select one complete original profile
def ReadRevMembers(FeatureValue: FeatureStep, SketchValue: Sketch) -> tuple[str, ...]:
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
        or not 1 <= len(Profile) <= 4
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
    return Profile


# only the selected whole profile may contribute to a live native sketch source
def CheckRevProfile(FeatureValue: FeatureStep, SketchValue: Sketch) -> None:
    ProfileIds = set(ReadRevMembers(FeatureValue, SketchValue))
    Origin = SketchValue.provenance
    if (
        Origin is None
        or Origin.adapter != "fusion.f3d"
        or SketchValue.id != f"fusion-sketch-{Origin.native_id}"
        or SketchValue.suppressed
        or SketchValue.constraints
        or SketchValue.parameter_ids
        or SketchValue.attributes.get("freecad")
        or len({Entity.id for Entity in SketchValue.entities})
        != len(SketchValue.entities)
    ):
        raise ValueError("FreeCAD editable Revolve sketch source is unsupported")
    for Entity in SketchValue.entities:
        Evidence = Entity.provenance
        if (
            Entity.fixed
            or Evidence is None
            or Evidence.adapter != "fusion.f3d"
            or Entity.id != f"fusion-sketch-entity-{Evidence.native_id}"
            or (
                Entity.id in ProfileIds
                and (
                    Entity.construction
                    or not isinstance(
                        Entity.geometry, (LineGeometry, ArcGeometry, CircleGeometry)
                    )
                )
            )
            or (
                Entity.id not in ProfileIds
                and not isinstance(Entity.geometry, PointGeometry)
            )
        ):
            raise ValueError("FreeCAD editable Revolve sketch entity is unsupported")
    Profile = ReadRevProfile(FeatureValue, SketchValue)
    if isinstance(Profile, tuple):
        ReadRingInput(SketchValue)
    else:
        from convert.adapters.freecad.EditRead.Sketch.SavedIncidence import (
            CheckIncidence,
        )

        CheckIncidence(SketchValue.entities)
        if isinstance(Profile, CircleGeometry) and GetCenterPoint(SketchValue) is None:
            raise ValueError("FreeCAD editable Revolve circle center is unresolved")
