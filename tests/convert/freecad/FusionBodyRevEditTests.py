from dataclasses import replace as Replace
from math import radians as Radians

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad.EditBodyRev.ApplyBodyRevEdit import ApplyBodyRev
from convert.adapters.freecad.EditBodyRev.BodyAxisEdit import KBodyAxisEdit
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import ReadBodyRev
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath
from tests.convert.freecad.FusionBodyRevPlanTests import KBodyRevCases


# the signed extrusion still selects its sketch plane rim after neutral roundtrip
@KRequiresCodec
@Pytest.mark.parametrize("SampleName", tuple(Value[0] for Value in KBodyRevCases))
def TestRevDepth(SampleName: str) -> None:
    DocValue = OpenDocument(KStudyPath / SampleName, StrictMode=False)
    PlanValue = ReadBodyRev(DocValue, DocValue.feature_timeline[-1])
    assert PlanValue is not None
    Source, Profile = DocValue.sketches
    Inputs = (Source, Profile, PlanValue.SourceFrame, PlanValue.ProfileFrame)
    assert (
        ApplyBodyRev(
            DocValue, PlanValue, *Inputs, (5.0, "5 mm"), (Radians(73.0), "73 deg")
        )
        is DocValue
    )
    Edited = ApplyBodyRev(
        DocValue, PlanValue, *Inputs, (-3.0, "-3 mm"), (Radians(-360.0), "-360 deg")
    )
    Saved = CadDocument.from_json(Edited.to_json())
    Updated = ReadBodyRev(Saved, Saved.feature_timeline[-1])
    assert Updated is not None and Updated.AxisEdgeId != PlanValue.AxisEdgeId
    assert (
        Updated.AxisLineId == PlanValue.AxisLineId
        and Updated.AxisStart == PlanValue.AxisStart
    )
    assert Updated.Extrude.DistanceMm == -3.0 and Updated.Revolve.AngleDeg == -360.0
    assert Saved.selections[0].attributes == DocValue.selections[0].attributes
    assert Saved.selections[0].provenance == DocValue.selections[0].provenance
    assert Saved.brep_payloads == DocValue.brep_payloads
    Restored = ApplyBodyRev(
        Saved, Updated, *Inputs, (5.0, "5 mm"), (Radians(73.0), "73 deg")
    )
    Again = ReadBodyRev(Restored, Restored.feature_timeline[-1])
    assert Again is not None and Again.AxisEdgeId == PlanValue.AxisEdgeId
    BadMeta = {
        MetaKey: Value
        for MetaKey, Value in Saved.metadata.items()
        if MetaKey != KBodyAxisEdit
    }
    assert (
        ReadBodyRev(Replace(Saved, metadata=BadMeta), Saved.feature_timeline[-1])
        is None
    )


# a common rigid pose keeps the source edge coplanar and rotates the extrusion direction
@KRequiresCodec
def TestRevPose() -> None:
    DocValue = OpenDocument(KStudyPath / KBodyRevCases[0][0], StrictMode=False)
    PlanValue = ReadBodyRev(DocValue, DocValue.feature_timeline[-1])
    assert PlanValue is not None
    Source, Profile = DocValue.sketches
    NewFrame = Transform(
        SpaceVector(3.0, 40.0, 0.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
    )
    Controls = ((5.0, "5 mm"), (Radians(73.0), "73 deg"))
    Edited = ApplyBodyRev(
        DocValue, PlanValue, Source, Profile, NewFrame, NewFrame, *Controls
    )
    Updated = ReadBodyRev(Edited, Edited.feature_timeline[-1])
    assert Updated is not None and Updated.Extrude.Direction == NewFrame.z_axis
    assert Updated.AxisStart == SpaceVector(3.0, 40.0, 30.0)
    assert Updated.AxisEnd == NewFrame.origin
    assert tuple(Value.topology.volume for Value in Edited.bodies) == tuple(
        Value.topology.volume for Value in DocValue.bodies
    )
    with Pytest.raises(ValueError, match="outside the sketch plane"):
        _ = ApplyBodyRev(
            DocValue,
            PlanValue,
            Source,
            Profile,
            NewFrame,
            PlanValue.ProfileFrame,
            *Controls,
        )


# a tangent side remains on the selected axis without creating degenerate topology
@KRequiresCodec
def TestRevTangent() -> None:
    DocValue = OpenDocument(KStudyPath / KBodyRevCases[0][0], StrictMode=False)
    PlanValue = ReadBodyRev(DocValue, DocValue.feature_timeline[-1])
    assert PlanValue is not None
    Source, Profile = DocValue.sketches
    SourceFrame = Replace(PlanValue.SourceFrame, origin=SpaceVector(-8.0, 0.0, 0.0))
    Edited = ApplyBodyRev(
        DocValue,
        PlanValue,
        Source,
        Profile,
        SourceFrame,
        PlanValue.ProfileFrame,
        (5.0, "5 mm"),
        (Radians(73.0), "73 deg"),
    )
    Updated = ReadBodyRev(Edited, Edited.feature_timeline[-1])
    assert Updated is not None and Updated.AxisStart == SpaceVector(-8.0, 30.0, 0.0)
    Topology = Edited.bodies[-1].topology
    assert (
        Topology.solid_count,
        Topology.face_count,
        Topology.edge_count,
        Topology.vertex_count,
    ) == (1, 5, 9, 6)
