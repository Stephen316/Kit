from dataclasses import replace as Replace

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad.EditExtBody import IsEditExtBody
from convert.adapters.freecad.EditExtDepth import GetEditDepth
from convert.adapters.freecad.EditExtRing import GetEditRing, GetRingPoints
from convert.adapters.freecad.EditExtSolid import BuildEditSolid
from convert.adapters.freecad.EditRing.RingChange import CheckRingEdit, SyncRingEdit
from convert.adapters.freecad.EditRing.RingEndpoints import ReadRingEnds
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the rectangle control provides an independently measured saved prism
KRectangleCase = "thinextrudes-c1632bcb5efe"


# a shared capture keeps synthetic geometry mutations tied to genuine source identities
def ReadRectangle() -> tuple[CadDocument, Sketch]:
    DocValue = OpenDocument(
        KStudyPath / KRectangleCase / "ordinary_rectangle_control.f3d", StrictMode=False
    )
    return DocValue, DocValue.sketches[0]


# each tracked source ring must reconstruct the exact neutral body in profile order
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Folder", "Capture"),
    (
        (KRectangleCase, "ordinary_rectangle_control"),
        ("parametertexts-d16f951482fc", "model_favorite_false"),
        ("parametertexts-d16f951482fc", "model_favorite_true"),
        ("parametertexts-d16f951482fc", "model_multiline_comment"),
    ),
)
def CheckSourceRing(Folder: str, Capture: str) -> None:
    DocValue = OpenDocument(KStudyPath / Folder / f"{Capture}.f3d", StrictMode=False)
    StepValue = DocValue.feature_timeline[-1]
    SketchValue = DocValue.sketches[0]
    Definition = StepValue.definition
    assert isinstance(Definition, DistanceExtrude)
    Profile = GetEditRing(StepValue, SketchValue)
    assert Profile is not None and len(Profile) == 4
    Entities = {Value.id: Value for Value in SketchValue.entities}
    assert Profile == tuple(
        Entities[Identity].geometry
        for Identity in SketchValue.closed_profile_entity_ids[0]
    )
    assert GetRingPoints(SketchValue) == frozenset(
        {
            "fusion-sketch-entity-228",
            "fusion-sketch-entity-230",
            "fusion-sketch-entity-232",
            "fusion-sketch-entity-234",
        }
    )
    DepthMm = GetEditDepth(StepValue, Definition, DocValue.parameters)
    assert DepthMm is not None
    BodyValue = DocValue.bodies[0]
    FrameValue = DocValue.support_planes[0].transform
    assert IsEditExtBody(BodyValue, DocValue.brep, Profile, FrameValue, DepthMm)
    Model, Volume, SurfaceArea, Bounds = BuildEditSolid(
        BodyValue.id, FrameValue, Profile, -DepthMm
    )
    assert DocValue.brep is not None
    assert Model.bodies[0].id == DocValue.brep.bodies[0].id
    assert (
        Volume == BodyValue.topology.volume
        and SurfaceArea == BodyValue.topology.surface_area
    )
    assert Bounds.minimum.z == -DepthMm and Bounds.maximum.z == 0.0


# coincident unrelated points cannot substitute for a proven shared native endpoint
@KRequiresCodec
def CheckRingPoint() -> None:
    DocValue, SketchValue = ReadRectangle()
    StepValue = DocValue.feature_timeline[-1]
    Entities = tuple(
        (
            Replace(
                Value,
                attributes={
                    **Value.attributes,
                    "fusion.line_native_point_ids": (205, 230),
                },
            )
            if Value.id == "fusion-sketch-entity-236"
            else Value
        )
        for Value in SketchValue.entities
    )
    assert GetEditRing(StepValue, Replace(SketchValue, entities=Entities)) is None
    assert (
        GetEditRing(
            Replace(
                StepValue,
                attributes={**StepValue.attributes, "fusion.profile_portions": ()},
            ),
            SketchValue,
        )
        is None
    )
    assert (
        GetEditRing(
            Replace(
                StepValue,
                attributes={
                    **StepValue.attributes,
                    "fusion.profile_native_directions": (0, 0, 0, True),
                },
            ),
            SketchValue,
        )
        is None
    )


# one source point moves with both incident lines without relying on coordinate lookup
def MoveRingCorner(Original: Sketch, NewPoint: PlaneVector) -> Sketch:
    PointId = "fusion-sketch-entity-232"
    Entities: list[SketchEntity] = []
    for Value in Original.entities:
        Geometry = Value.geometry
        if Value.id == PointId:
            Geometry = PointGeometry(NewPoint)
        elif isinstance(Geometry, LineGeometry):
            StartId, EndId = ReadRingEnds(Value)
            Geometry = LineGeometry(
                NewPoint if StartId == PointId else Geometry.start,
                (
                    PlaneVector(NewPoint.x + 1e-10, NewPoint.y)
                    if EndId == PointId
                    else Geometry.end
                ),
            )
        Entities.append(Replace(Value, geometry=Geometry))
    return Replace(Original, entities=tuple(Entities))


# roundoff normalization preserves an exact concave ring and all stable body topology ids
@KRequiresCodec
def CheckRingSync() -> None:
    DocValue, Original = ReadRectangle()
    StepValue = DocValue.feature_timeline[-1]
    Edited = MoveRingCorner(Original, PlaneVector(10, 10))
    assert GetEditRing(StepValue, Edited) is None
    Synced = SyncRingEdit(Original, Edited)
    CheckRingEdit(Original, Synced)
    assert SyncRingEdit(Original, Original) is Original
    Profile = GetEditRing(StepValue, Synced)
    assert Profile is not None and DocValue.brep is not None
    Model, Volume, _, Bounds = BuildEditSolid(
        DocValue.bodies[0].id, DocValue.support_planes[0].transform, Profile, -30
    )
    assert tuple(Value.id for Value in Model.edges) == tuple(
        Value.id for Value in DocValue.brep.edges
    )
    assert Volume == 10500
    assert (Bounds.minimum.z, Bounds.maximum.z) == (-30, 0)
    with Pytest.raises(ValueError, match="same incidence"):
        _ = SyncRingEdit(Original, MoveRingCorner(Original, PlaneVector(20, -10)))


# unchanged neutral profile intent excludes changes to an unselected helper or entity metadata
@KRequiresCodec
def CheckRingGuards() -> None:
    _, Original = ReadRectangle()
    First = Original.entities[0]
    with Pytest.raises(ValueError, match="unrelated sketch geometry"):
        CheckRingEdit(
            Original,
            Replace(
                Original,
                entities=(Replace(First, geometry=PointGeometry(PlaneVector(2, 3))),)
                + Original.entities[1:],
            ),
        )
    with Pytest.raises(ValueError, match="entity identity"):
        _ = SyncRingEdit(
            Original,
            Replace(
                Original,
                entities=(Replace(First, construction=True),) + Original.entities[1:],
            ),
        )
