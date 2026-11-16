from dataclasses import replace as Replace

from interchange import (
    Body,
    BooleanOperation,
    CadDocument,
    CadSource,
    Configuration,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    ScopedExtrusionFeature,
)
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


# identical affected bodies can belong to two distinct authored scope policies
def CheckScopeWire() -> None:
    ShapeValue = ExtrusionFeature(None, ExtrusionEndCondition.THROUGH_ALL)
    Ordinary = ToData(ShapeValue)
    assert isinstance(Ordinary, dict)
    assert Ordinary["$type"] == "ExtrusionFeature"
    assert "scope_mode" not in Ordinary
    assert FromData(Ordinary) == ShapeValue

    BodyIds = ("body-a", "body-b")
    AllBodies = ScopedExtrusionFeature(ShapeValue, "all_applicable", (), BodyIds)
    Explicit = ScopedExtrusionFeature(ShapeValue, "explicit", BodyIds, BodyIds)
    AllRecord = ToData(AllBodies)
    Selected = ToData(Explicit)
    assert isinstance(AllRecord, dict) and isinstance(Selected, dict)
    assert AllRecord["$type"] == Selected["$type"] == "ScopedExtrusionFeature"
    assert AllRecord["selected_body_ids"] != Selected["selected_body_ids"]
    assert AllRecord["affected_body_ids"] == Selected["affected_body_ids"]
    assert FromData(AllRecord) == AllBodies
    assert FromData(Selected) == Explicit


# resolved bodies and authored selections both require actual design body identities
def CheckScopeRefs() -> None:
    ShapeValue = ExtrusionFeature(None, ExtrusionEndCondition.THROUGH_ALL)
    CutValue = FeatureStep(
        "part-cut",
        "Cut",
        FeatureKind.EXTRUSION,
        1,
        operation=BooleanOperation.CUT,
        definition=ScopedExtrusionFeature(
            ShapeValue, "explicit", ("body-a", "body-b"), ("body-a",)
        ),
    )
    Document = CadDocument(
        source=CadSource("sldprt", "scope.sldprt", "0" * 64),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(CutValue,),
        bodies=(Body("body-a", "A", CutValue.id), Body("body-b", "B", CutValue.id)),
    )
    assert Document.validate() == ()
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored.feature_timeline == Document.feature_timeline
    assert Replace(Document, bodies=Document.bodies[:1]).validate() == (
        "scoped extrusion part-cut references missing bodies ['body-b']",
    )
