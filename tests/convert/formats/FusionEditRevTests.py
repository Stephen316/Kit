# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

import pytest as Pytest

from convert import open_document as OpenDocument
from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditableRev import ReadEditRevolve
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the captured angular contrast separates signed and centered controls
KModeFolder = "revolvemodes-8eb734486235"


# saved controls retain native identities independently of recomputed angles
def ReadRevCase(Folder: str, Capture: str) -> CadDocument:
    return OpenDocument(KStudyPath / Folder / f"{Capture}.f3d", strict=False)


# seven supported source controls must seed an exact portable body and native extent
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Folder", "Capture", "AngleDeg", "Scale", "Midpoint"),
    (
        ("models-97a5e41e2ba7", "revolve_full", 360, 1, 0),
        ("models-97a5e41e2ba7", "revolve_partial", 65, 1, 0),
        (KModeFolder, "positive", 65, 1, 0),
        (KModeFolder, "negative", -75, 1, 0),
        (KModeFolder, "axis_x", 65, 1, 0),
        (KModeFolder, "symmetric", 130, 2, 0),
        (KModeFolder, "two_sided", 85, 1, 17.5),
    ),
)
def CheckRevPlan(
    Folder: str, Capture: str, AngleDeg: float, Scale: float, Midpoint: float
) -> None:
    DocValue = ReadRevCase(Folder, Capture)
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    assert isinstance(Definition, AngularRevolve)
    PlanValue = ReadEditRevolve(DocValue, Feature)
    assert PlanValue is not None
    assert PlanValue.SketchId == Feature.sketch_id
    assert PlanValue.AngleParamId == Definition.AlongParameterId
    assert PlanValue.AgainstParamId == Definition.AgainstParameterId
    assert PlanValue.AxisOrigin == Definition.AxisOrigin
    assert PlanValue.AxisDirection == Definition.AxisDirection
    assert PlanValue.AngleDeg == Pytest.approx(AngleDeg)
    assert PlanValue.AngleScale == Scale
    assert PlanValue.Symmetric == (Definition.SideMode != "one_sided")
    assert PlanValue.PlacementAngleDeg == Pytest.approx(Midpoint)
    assert DocValue.brep is not None and BrepModelBrep(DocValue.brep)


# live origins do not replace plane termination or independently selected axis sketches
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Folder", "Capture"),
    (
        ("revolveto-b1d196f65c46", "positive_plane"),
        ("revolveto-b1d196f65c46", "two_planes"),
        ("revolveaxes-a83b542c4a07", "sketch_line"),
        ("analytic-86a12b291d0a", "analytic"),
    ),
)
def CheckRevCarrier(Folder: str, Capture: str) -> None:
    DocValue = ReadRevCase(Folder, Capture)
    assert DocValue.brep is not None
    assert ReadEditRevolve(DocValue, DocValue.feature_timeline[-1]) is None


# stale native ownership or geometry cannot promote an otherwise valid angular control
@KRequiresCodec
def CheckRevGuards() -> None:
    DocValue = ReadRevCase(KModeFolder, "positive")
    Feature = DocValue.feature_timeline[-1]
    assert ReadEditRevolve(DocValue, Feature) is not None
    (BodyValue,) = DocValue.bodies
    Stale = Replace(BodyValue, topology=Replace(BodyValue.topology, volume=1.0))
    assert ReadEditRevolve(Replace(DocValue, bodies=(Stale,)), Feature) is None
    (AxisPick,) = DocValue.selections
    WrongAxis = Replace(AxisPick, query={**AxisPick.query, "axis": "X"})
    assert ReadEditRevolve(Replace(DocValue, selections=(WrongAxis,)), Feature) is None
    (Angle,) = DocValue.parameters
    WrongAngle = Replace(
        Angle, attributes={**Angle.attributes, "fusion.owner_object_id": 999}
    )
    assert ReadEditRevolve(Replace(DocValue, parameters=(WrongAngle,)), Feature) is None
    Changed = Replace(
        Feature, attributes={**Feature.attributes, "fusion.profile_descriptor_id": 0}
    )
    assert (
        ReadEditRevolve(
            Replace(
                DocValue, feature_timeline=DocValue.feature_timeline[:-1] + (Changed,)
            ),
            Changed,
        )
        is None
    )
    Metadata = {
        KeyValue: Value
        for KeyValue, Value in DocValue.metadata.items()
        if KeyValue != "fusion.body_inventory"
    }
    assert ReadEditRevolve(Replace(DocValue, metadata=Metadata), Feature) is None
